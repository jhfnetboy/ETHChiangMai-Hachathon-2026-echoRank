// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/CommunityNFT.sol";

contract CommunityNFTTest is Test {
    CommunityNFT public nft;
    address public owner = address(1);
    address public user1 = address(2);
    address public user2 = address(3);

    function setUp() public {
        vm.prank(owner);
        nft = new CommunityNFT("Test NFT", "TNFT", owner);
    }

    function testBatchMint() public {
        address[] memory recipients = new address[](2);
        recipients[0] = user1;
        recipients[1] = user2;

        string[] memory uris = new string[](2);
        uris[0] = "uri1";
        uris[1] = "uri2";

        vm.prank(owner);
        nft.batchMint(recipients, uris);

        assertEq(nft.balanceOf(user1), 1);
        assertEq(nft.balanceOf(user2), 1);
        assertEq(nft.tokenURI(0), "uri1");
        assertEq(nft.tokenURI(1), "uri2");
    }

    function testOnlyOwnerCanMint() public {
        address[] memory recipients = new address[](1);
        recipients[0] = user1;
        string[] memory uris = new string[](1);
        uris[0] = "uri1";

        vm.expectRevert(
            abi.encodeWithSelector(
                Ownable.OwnableUnauthorizedAccount.selector,
                user1
            )
        );
        vm.prank(user1);
        nft.batchMint(recipients, uris);
    }
}
