#!/bin/bash
# debug_mint.sh
# Debugs the mint.ts script by loading env and running it manually

# 1. Load Root .env
set -a
source .env
set +a

# 2. Check Private Key
if [[ "$AI_AGENT_PRIVATE_KEY" =~ ^[0-9]+$ ]]; then
    echo "Converting Decimal Private Key to Hex..."
    # Convert decimal to hex using python for reliability
    HEX_KEY=$(python3 -c "print(hex($AI_AGENT_PRIVATE_KEY))")
    export AI_AGENT_PRIVATE_KEY=$HEX_KEY
    echo "Private Key Converted: ${AI_AGENT_PRIVATE_KEY:0:6}..."
else
    echo "Private Key seems to be in Hex/String format."
fi

# 3. Helpers
MINT_SCRIPT="scripts/mint-service/mint.ts"
NFT_CONTRACT="0x0c8EcCD5B98AfdBae8b282Ae98F4f4FFCcF9e560" 

# 4. User Params (Hardcoded from failed log for repro)
TO_ADDR="0xEcAACb915f7D92e9916f449F7ad42BD0408733c9"
URI="data:application/json;base64,eyJuYW1lIjogIkVUSERlbnZlciAyMDI2IHwgRGV2Zm9saW8iLCAiZGVzY3JpcHRpb24iOiAiU0JUIGZvciBwYXJ0aWNpcGF0aW5nIGluIEVUSERlbnZlciAyMDI2IHwgRGV2Zm9saW8uIFZlcmlmaWVkIGJ5IEVjaG9SYW5rIEFJLiIsICJpbWFnZSI6ICJpcGZzOi8vYmFma3JlaWhxbXNueW40czVydDZubnlyeGJ3YXVmem1yc3IyeGZiajR5ZXFnaTZxZHIzNXVtenhpYXkiLCAiYXR0cmlidXRlcyI6IFt7InRyYWl0X3R5cGUiOiAiVHlwZSIsICJ2YWx1ZSI6ICJWb2ljZSBGZWVkYmFjayBSZXdhcmQifSwgeyJ0cmFpdF90eXBlIjogIkNvbmZpZGVuY2UiLCAidmFsdWUiOiAiMC42NSJ9LCB7InRyYWl0X3R5cGUiOiAiU2VudGltZW50IiwgInZhbHVlIjogIlNBRCJ9XX0="

# 5. Run
echo "Running Mint Script..."
cd scripts/mint-service
pnpm tsx mint.ts --to "$TO_ADDR" --uri "$URI" --soulbound true --contract "$NFT_CONTRACT"
