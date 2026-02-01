// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title CommunityNFT
 * @dev ERC721 NFT for community airdrops with batch minting and flexible metadata.
 */
contract CommunityNFT is ERC721URIStorage, Ownable {
    uint256 private _nextTokenId;

    event CommunityNFTMinted(address indexed recipient, uint256 indexed tokenId, string tokenURI);

    constructor(
        string memory name,
        string memory symbol,
        address initialOwner
    ) ERC721(name, symbol) Ownable(initialOwner) {}

    /**
     * @dev Batch mint NFTs to multiple recipients with their respective URIs.
     * @param recipients Array of wallet addresses to receive the NFTs.
     * @param tokenURIs Array of metadata URIs (including image, description, activity name etc.)
     */
    function batchMint(
        address[] calldata recipients,
        string[] calldata tokenURIs
    ) external onlyOwner {
        require(recipients.length == tokenURIs.length, "CommunityNFT: Length mismatch");

        for (uint256 i = 0; i < recipients.length; i++) {
            _safeMintInternal(recipients[i], tokenURIs[i]);
        }
    }

    /**
     * @dev Internal function to mint a single NFT.
     */
    function _safeMintInternal(address to, string memory uri) internal {
        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);
        emit CommunityNFTMinted(to, tokenId, uri);
    }
}
