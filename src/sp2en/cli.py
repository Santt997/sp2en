# sp2en

from pathlib import Path
import json
import sys
import re
import logging
import argparse
import difflib
from typing import Any


def main() -> None:

    # =========================================================
    # CLI
    # =========================================================

    parser = argparse.ArgumentParser(
        description='Apply contextual replacements to .ipynb files'
    )

    parser.add_argument(
        'target',
        nargs='?',
        default='.',
        help='TargetDirectory'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes !w writing fs'
    )

    args = parser.parse_args()


    # Logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                Path.home() / 'sp2en_script.log',
                encoding='utf-8'
            )
        ]
    )

    logger: logging.Logger = logging.getLogger(__name__)


    # Paths

    root: Path = Path(
        args.target
    ).expanduser().resolve()

    script_dir: Path = Path(
        __file__
    ).resolve().parent

    rules_dir: Path = script_dir / 'rules'

    logger.info('=========================================================')
    logger.info('sp2en starting...')
    logger.info('ROOT: %s', root)
    logger.info('SCRIPT_DIR: %s', script_dir)
    logger.info('RULES_DIR: %s', rules_dir)
    logger.info('DRY_RUN: %s', args.dry_run)


    # Validation

    if not root.exists():

        logger.error(
            'Target directory does not exist: %s',
            root
        )

        sys.exit(1)

    if not root.is_dir():

        logger.error(
            'Target is not a directory: %s',
            root
        )

        sys.exit(1)


    # Helpers

    def read_lines(
        path: Path,
        required: bool = True
    ) -> list[str]:

        if not path.exists():

            if required:
                raise FileNotFoundError(path)

            logger.warning(
                'Optional file not found: %s',
                path
            )

            return []

        lines = path.read_text(
            encoding='utf-8',
            errors='replace'
        ).splitlines()

        return [
            line.rstrip('\n')
            for line in lines
        ]


    # Rules

    class Rules:

        def __init__(
            self,
            name: str
        ) -> None:

            self.name = name

            self.dir = rules_dir / name

            self.olds = read_lines(
                self.dir / 'olds.txt',
                required=False
            )

            self.news = read_lines(
                self.dir / 'news.txt',
                required=False
            )

            self.olds_literal = read_lines(
                self.dir / 'olds_literal.txt',
                required=False
            )

            self.news_literal = read_lines(
                self.dir / 'news_literal.txt',
                required=False
            )

            self.literal_pairs: list[tuple[str, str]] = [
                (o, n)
                for o, n in zip(
                    self.olds_literal,
                    self.news_literal
                )
                if o
            ]

            self.word_pairs: list[tuple[str, str]] = [
                (o, n)
                for o, n in zip(
                    self.olds,
                    self.news
                )
                if o
            ]

            self.literal_pairs = sorted(
                self.literal_pairs,
                key=lambda t: len(t[0]),
                reverse=True
            )

            self.word_pairs = sorted(
                self.word_pairs,
                key=lambda t: len(t[0]),
                reverse=True
            )

            literal_old_set = {
                o for o, _ in self.literal_pairs
            }

            self.word_pairs = [
                (o, n)
                for o, n in self.word_pairs
                if o not in literal_old_set
            ]

            logger.info(
                '[%s] word replacements: %d',
                self.name,
                len(self.word_pairs)
            )

            logger.info(
                '[%s] literal replacements: %d',
                self.name,
                len(self.literal_pairs)
            )


    markdown_rules = Rules('markdown')
    python_rules = Rules('python')
    julia_rules = Rules('julia')


    # Regex

    CODE_BLOCK_PATTERN = re.compile(
        r'```.*?```',
        re.DOTALL
    )

    INLINE_MATH_PATTERN = re.compile(
        r'\$(?!\$)(.*?)\$',
        re.DOTALL
    )

    BLOCK_MATH_PATTERN = re.compile(
        r'\$\$(.*?)\$\$',
        re.DOTALL
    )

    PLACEHOLDER_TEMPLATE = '__SP2EN_BLOCK_{}__'


    def word_pattern(
        old: str
    ) -> re.Pattern[str]:

        return re.compile(
            rf'\b{re.escape(old)}\b',
            re.IGNORECASE
        )


    # ProtectedBlocks

    def protect_pattern(
        text: str,
        pattern: re.Pattern[str],
        placeholders: dict[str, str]
    ) -> str:

        def replacer(
            match: re.Match[str]
        ) -> str:

            key = PLACEHOLDER_TEMPLATE.format(
                len(placeholders)
            )

            placeholders[key] = match.group(0)

            return key

        return pattern.sub(
            replacer,
            text
        )


    def protect_special_blocks(
        text: str
    ) -> tuple[str, dict[str, str]]:

        placeholders: dict[str, str] = {}

        out = text

        # fenced code blocks

        out = protect_pattern(
            out,
            CODE_BLOCK_PATTERN,
            placeholders
        )

        # $$ math $$

        out = protect_pattern(
            out,
            BLOCK_MATH_PATTERN,
            placeholders
        )

        # $ math $

        out = protect_pattern(
            out,
            INLINE_MATH_PATTERN,
            placeholders
        )

        return out, placeholders


    def restore_special_blocks(
        text: str,
        placeholders: dict[str, str]
    ) -> str:

        out = text

        for key, value in placeholders.items():

            out = out.replace(
                key,
                value
            )

        return out


    # Replacements

    def apply_replacements(
        text: str,
        rules: Rules,
        protect_special: bool = False
    ) -> tuple[str, list[str]]:

        out = text

        hits: list[str] = []

        placeholders: dict[str, str] = {}

        # protect mad blocks

        if protect_special:

            out, placeholders = protect_special_blocks(out)

        # literalReplacements

        for old, new in rules.literal_pairs:

            if old in out:

                count = out.count(old)

                hits.append(
                    f'literal: {old!r} -> {new!r} ({count} hits)'
                )

                out = out.replace(
                    old,
                    new
                )

        # word replacements

        for old, new in rules.word_pairs:

            pattern = word_pattern(old)

            count = len(
                pattern.findall(out)
            )

            if count:

                hits.append(
                    f'word: {old!r} -> {new!r} ({count} hits)'
                )

                out = pattern.sub(
                    new,
                    out
                )

        # restore protected blocks

        if protect_special:

            out = restore_special_blocks(
                out,
                placeholders
            )

        return out, hits

    # Diff

    def compact_diff(
        before: str,
        after: str,
        max_lines: int = 20
    ) -> str:

        diff = difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            lineterm=''
        )

        lines = list(diff)

        if len(lines) > max_lines:

            lines = lines[:max_lines]

            lines.append('...')

        return '\n'.join(lines)


    # Nb lang

    def notebook_language(
        nb: dict[str, Any]
    ) -> str:

        metadata = nb.get(
            'metadata',
            {}
        )

        # kernelspec

        kernelspec = metadata.get(
            'kernelspec',
            {}
        )

        language = kernelspec.get(
            'language'
        )

        if language:
            return str(language).lower()

        # language_info

        language_info = metadata.get(
            'language_info',
            {}
        )

        language = language_info.get(
            'name'
        )

        if language:
            return str(language).lower()

        return 'unknown'

    # Find nbs

    ipynb_files: list[Path] = sorted(
        root.rglob('*.ipynb')
    )

    logger.info(
        'Found %d notebook(s)',
        len(ipynb_files)
    )

    if not ipynb_files:

        logger.warning(
            'No .ipynb files found'
        )

        sys.exit(0)

    for path in ipynb_files:

        logger.info(
            'NOTEBOOK: %s',
            path
        )


    # Processing

    changed_files: int = 0
    changed_cells: int = 0
    processed_files: int = 0
    skipped_files: int = 0

    for ipynb in ipynb_files:

        logger.info('---------------------------------------------------------')
        logger.info('Processing: %s', ipynb)

        try:

            original_text = ipynb.read_text(
                encoding='utf-8'
            )

            nb = json.loads(
                original_text
            )

        except Exception as e:

            logger.warning(
                'Skipping %s: %s',
                ipynb,
                e
            )

            skipped_files += 1

            continue

        processed_files += 1

        notebook_lang = notebook_language(nb)

        logger.info(
            'Notebook language: %s',
            notebook_lang
        )

        file_changed = False
        file_cell_changes = 0

        cells = nb.get(
            'cells',
            []
        )

        logger.info(
            'Cells found: %d',
            len(cells)
        )

        for idx, cell in enumerate(cells):

            cell_type = cell.get(
                'cell_type'
            )

            source: Any = cell.get(
                'source'
            )

            if not source:
                continue

            # MARKDOWN

            if cell_type == 'markdown':

                rules = markdown_rules

                protect_special = True

            # CODE

            elif cell_type == 'code':

                # python

                if notebook_lang == 'python':

                    logger.info(
                        'SKIP | python code cell %d',
                        idx
                    )

                    continue

                # julia

                elif notebook_lang == 'julia':

                    rules = julia_rules

                    protect_special = False

                # unknown

                else:

                    logger.info(
                        'SKIP | unknown language code cell %d',
                        idx
                    )

                    continue

            else:

                continue

            # process

            original = ''.join(source)

            new, hits = apply_replacements(
                original,
                rules=rules,
                protect_special=protect_special
            )

            if hits:

                logger.info(
                    '%s | %s cell %d | %d replacement group(s)',
                    ipynb.name,
                    cell_type,
                    idx,
                    len(hits)
                )

                for hit in hits:

                    logger.info(
                        '  %s',
                        hit
                    )

            if new != original:

                logger.info(
                    'CHANGED | %s | %s cell %d',
                    ipynb.name,
                    cell_type,
                    idx
                )

                logger.info(
                    'DIFF:\n%s',
                    compact_diff(
                        original,
                        new
                    )
                )

                cell['source'] = (
                    new.splitlines(
                        keepends=True
                    )
                    if '\n' in new
                    else [new]
                )

                file_changed = True

                file_cell_changes += 1

                changed_cells += 1

        # save

        if file_changed:

            backup = ipynb.with_suffix(
                ipynb.suffix + '.bak'
            )

            if not backup.exists():

                if not args.dry_run:

                    backup.write_text(
                        original_text,
                        encoding='utf-8'
                    )

                logger.info(
                    'Backup created: %s',
                    backup
                )

            if args.dry_run:

                logger.info(
                    'DRY_RUN | Changes NOT written: %s',
                    ipynb.name
                )

            else:

                ipynb.write_text(
                    json.dumps(
                        nb,
                        indent=1,
                        ensure_ascii=False
                    ),
                    encoding='utf-8'
                )

                logger.info(
                    'SAVED | %s | %d changed cell(s)',
                    ipynb.name,
                    file_cell_changes
                )

            changed_files += 1

        else:

            logger.info(
                'NO CHANGES | %s',
                ipynb.name
            )


    # Summ

    logger.info('=========================================================')
    logger.info('DONE')
    logger.info('Processed files : %d', processed_files)
    logger.info('Skipped files   : %d', skipped_files)
    logger.info('Changed files   : %d', changed_files)
    logger.info('Changed cells   : %d', changed_cells)
    logger.info('=========================================================')

if __name__ == '__main__':
    main()