/**
 * Base Sepolia (84532) — StakingFactory + ajan havuzları
 * Gerçek USDC: 0x036CbD53842c5426634e7929541eC2318f3dCF7e
 *
 * Kullanım:
 *   DEPLOYER_PRIVATE_KEY=0x... npm run deploy:sepolia
 */
const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

const AGENT_POOLS = require("./agent-pools");

const BASE_SEPOLIA_USDC = "0x036CbD53842c5426634e7929541eC2318f3dCF7e";
const USDC_DECIMALS = 6;

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const network = await hre.ethers.provider.getNetwork();
  const chainId = Number(network.chainId);

  if (chainId !== 84532) {
    throw new Error(`Beklenen chain 84532 (base-sepolia), gelen: ${chainId}`);
  }

  const usdcAddress = process.env.OAM_USDC_ADDRESS || BASE_SEPOLIA_USDC;
  console.log("USDC:", usdcAddress);
  console.log("Deployer:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("ETH balance:", hre.ethers.formatEther(balance));
  if (balance === 0n) {
    throw new Error("Deployer cüzdanında Base Sepolia ETH yok — faucet gerekli");
  }

  const StakingFactory = await hre.ethers.getContractFactory("StakingFactory");
  const factory = await StakingFactory.deploy(usdcAddress);
  await factory.waitForDeployment();
  const factoryAddress = await factory.getAddress();
  console.log("StakingFactory:", factoryAddress);

  const pools = {};
  for (const agent of AGENT_POOLS) {
    const tx = await factory.deployPool(agent.agentId, agent.tokenSymbol);
    await tx.wait();
    const poolAddress = await factory.getPool(agent.agentId);
    pools[agent.agentId] = {
      address: poolAddress,
      token_symbol: agent.tokenSymbol,
    };
    console.log(`Pool ${agent.agentId} -> ${poolAddress}`);
  }

  const payee = process.env.OAM_X402_PAYEE_ADDRESS || deployer.address;
  const deployment = {
    chain_id: chainId,
    network: "base-sepolia",
    rpc_url: process.env.OAM_ONCHAIN_RPC_URL || "https://sepolia.base.org",
    deployer: deployer.address,
    usdc: usdcAddress,
    factory: factoryAddress,
    pools,
    usdc_decimals: USDC_DECIMALS,
    x402_payee: payee,
    deployed_at: new Date().toISOString(),
  };

  const outDir = path.join(__dirname, "..", "..", "deployments");
  fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, "sepolia.json");
  fs.writeFileSync(outPath, JSON.stringify(deployment, null, 2));
  console.log("\nWrote", outPath);
  console.log("\nSunucu .env.server:");
  console.log("OAM_ONCHAIN_ENABLED=true");
  console.log("OAM_ONCHAIN_CHAIN_ID=84532");
  console.log("OAM_ONCHAIN_RPC_URL=https://sepolia.base.org");
  console.log("OAM_ONCHAIN_DEPLOYMENT=deployments/sepolia.json");
  console.log(`OAM_X402_PAYEE_ADDRESS=${payee}`);
  console.log("OAM_X402_DEV_ACCEPT_PROOF=false");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
