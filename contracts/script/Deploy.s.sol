// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/CommunityNFT.sol";

contract DeployCommunityNFT is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("OPERATOR_PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        string memory name = "Community Pass";
        string memory symbol = "CPASS";
        address initialOwner = vm.addr(deployerPrivateKey);

        CommunityNFT nft = new CommunityNFT(name, symbol, initialOwner);

        console.log("CommunityNFT deployed to:", address(nft));

        vm.stopBroadcast();
    }
}
