const { privateKeyToAccount } = require('viem/accounts');

const pkDecimal = "39512271710248888239882573016600305408296900873129360442509357140255876529595";
const pkHex = "0x" + BigInt(pkDecimal).toString(16);

console.log("Decimal:", pkDecimal);
console.log("Hex:", pkHex);

try {
    const account = privateKeyToAccount(pkHex);
    console.log("Address:", account.address);
} catch (e) {
    console.error("Error:", e.message);
}
