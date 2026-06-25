const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

const AGENT_POOLS = [
  { agentId: "oam.fetcher.local", tokenSymbol: "BMF-TKN" },
  { agentId: "oam.synthesizer.local", tokenSymbol: "CAV4-TKN" },
  { agentId: "oam.transformer.local", tokenSymbol: "DN-TKN" },
  { agentId: "oam.analyst.market.local", tokenSymbol: "MP-TKN" },
  { agentId: "oam.analyst.sentiment.local", tokenSymbol: "SR-TKN" },
  { agentId: "oam.fetcher.web.local", tokenSymbol: "WCP-TKN" },
];

const USDC_DECIMALS = 6;
const MINT_TO_DEPLOYER = 1_000_000n * 10n ** BigInt(USDC_DECIMALS);

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const network = await hre.ethers.provider.getNetwork();

  const MockUSDC = await hre.ethers.getContractFactory("MockUSDC");
  const usdc = await MockUSDC.deploy();
  await usdc.waitForDeployment();
  const usdcAddress = await usdc.getAddress();

  await (await usdc.mint(deployer.address, MINT_TO_DEPLOYER)).wait();

  const StakingFactory = await hre.ethers.getContractFactory("StakingFactory");
  const factory = await StakingFactory.deploy(usdcAddress);
  await factory.waitForDeployment();
  const factoryAddress = await factory.getAddress();

  const pools = {};
  for (const agent of AGENT_POOLS) {
    const tx = await factory.deployPool(agent.agentId, agent.tokenSymbol);
    const receipt = await tx.wait();
    const poolAddress = await factory.getPool(agent.agentId);
    pools[agent.agentId] = {
      address: poolAddress,
      token_symbol: agent.tokenSymbol,
    };
    console.log(`Pool ${agent.agentId} -> ${poolAddress} (tx ${receipt.hash})`);
  }

  const deployment = {
    chain_id: Number(network.chainId),
    network: hre.network.name,
    rpc_url: hre.network.config.url || "http://127.0.0.1:8545",
    deployer: deployer.address,
    usdc: usdcAddress,
    factory: factoryAddress,
    pools,
    usdc_decimals: USDC_DECIMALS,
    deployed_at: new Date().toISOString(),
  };

  const outDir = path.join(__dirname, "..", "..", "deployments");
  fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, "local.json");
  fs.writeFileSync(outPath, JSON.stringify(deployment, null, 2));
  console.log("Wrote", outPath);
  console.log("USDC minted to deployer:", deployer.address);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
