const hre = require("hardhat");

async function main() {
  const to = process.argv[2];
  const amount = process.argv[3] || "10000";
  if (!to) {
    console.error("Kullanım: node scripts/hardhat/mint_usdc.js 0xAdres [miktar_USDC]");
    process.exit(1);
  }

  const deployment = require("../../deployments/local.json");
  const usdc = await hre.ethers.getContractAt("MockUSDC", deployment.usdc);
  const decimals = deployment.usdc_decimals || 6;
  const wei = hre.ethers.parseUnits(amount, decimals);
  const tx = await usdc.mint(to, wei);
  await tx.wait();
  console.log(`Minted ${amount} USDC -> ${to}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
