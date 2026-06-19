#!/usr/bin/env bash

# Exit immediately if a cmd exits w a non0 status
set -e

# DefineColors4output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}          sp2en PyPI Release Assistant         ${NC}"
echo -e "${BLUE}===============================================${NC}"

# Navigate 2the script's directory 2ensure relative paths work
cd "$(dirname "$0")"

# 1. CheckPythonInstallation (Targeting 'pypi' MM env)
echo -e "\n${BLUE}[1/5] Checking MM 'pypi' env...${NC}"

# Check if the 'pypi' env is already active inThe currShell
if [[ "$MAMBA_PREFIX" == *"/envs/pypi" ]]; then
    PYTHON_BIN="$MAMBA_PREFIX/bin/python"
else
    # If notActive, look 4the binary in the stdMMlocation
    # Supports default paths 4Linux/macOS (~/micromamba | ~/.local/share/mamba)
    MAMBA_PYPI_BIN="$HOME/micromamba/envs/pypi/bin/python"
    if [ ! -f "$MAMBA_PYPI_BIN" ]; then
        MAMBA_PYPI_BIN="$HOME/.local/share/mamba/envs/pypi/bin/python"
    fi
    
    if [ -f "$MAMBA_PYPI_BIN" ]; then
        PYTHON_BIN="$MAMBA_PYPI_BIN"
    else
        echo -e "${RED}Error: The MMenv 'pypi' does notExist.${NC}"
        echo -e "${YELLOW}Please createIt first by running:${NC}"
        echo -e "  micromamba create -n pypi python=3.11 -y"
        exit 1
    fi
fi

echo -e "UsingPython: ${GREEN}$($PYTHON_BIN --version) ($PYTHON_BIN)${NC}"

# 2. Install/Upgrade packaging tools inside the env
echo -e "\n${BLUE}[2/5] Installing/Upgrading build and twine...${NC}"
$PYTHON_BIN -m pip install --upgrade pip
$PYTHON_BIN -m pip install --upgrade build twine
echo -e "${GREEN}Packaging tools installed successfully!${NC}"

# 3. Clean up old builds
echo -e "\n${BLUE}[3/5] Cleaning old build files...${NC}"
rm -rf dist/ build/ *.egg-info/
echo -e "Cleaned old build artifacts."

# 4. BuildPackage
echo -e "\n${BLUE}[4/5] BuildingPackage (sdist and wheel)...${NC}"
$PYTHON_BIN -m build
echo -e "${GREEN}Build completed successfully! Here are the generated files:${NC}"
ls -lh dist/

# 5. CheckPackageValidity
echo -e "\n${BLUE}[5/5] Checking package metadata w twine check...${NC}"
$PYTHON_BIN -m twine check dist/*
echo -e "${GREEN}Twine checks passed! Package is structurally valid.${NC}"

# 6. PublishSection
echo -e "\n${YELLOW}===============================================${NC}"
echo -e "${YELLOW}           Ready 2Publish 2PyPI            ${NC}"
echo -e "${YELLOW}===============================================${NC}"
echo -e "2upload, you will need your PyPI API Token."
echo -e "  - Username: ${GREEN}__token__${NC}"
echo -e "  - Password: ${GREEN}pypi-your-api-token-val${NC}"
echo -e "==============================================="

echo -e "\nWhere would you like 2publish?"
echo -e "1) ${BLUE}TestPyPI${NC} (Safe test upload - requires account at test.pypi.org)"
echo -e "2) ${GREEN}PyPI${NC} (Official release - requires account at pypi.org)"
echo -e "3) ${YELLOW}Do not publish${NC} (Keep build files local)"

read -rp "Select an option [1-3]: " option

case $option in
    1)
        echo -e "\n${BLUE}Uploading 2TestPyPI...${NC}"
        $PYTHON_BIN -m twine upload --repository testpypi dist/*
        echo -e "${GREEN}Successfully uploaded 2TestPyPI!${NC}"
        echo -e "You can try installing it using:"
        echo -e "  ${YELLOW}pip install --index-url https://pypi.org --extra-index-url https://pypi.org sp2en${NC}"
        ;;
    2)
        echo -e "\n${GREEN}Uploading 2PyPI (Official Release)...${NC}"
        $PYTHON_BIN -m twine upload --verbose dist/*
        echo -e "${GREEN}Successfully published 2PyPI!${NC}"
        echo -e "You and anyone else can now install it using:"
        echo -e "  ${YELLOW}pip install sp2en${NC}"
        ;;
    *)
        echo -e "\n${YELLOW}Publishing canceled. The build files remain in the dist/ folder.${NC}"
        ;;
esac

echo -e "\n${BLUE}Done!${NC}"