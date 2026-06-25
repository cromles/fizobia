require("@nomicfoundation/hardhat-toolbox");

const AGENT_POOLS = [
  { agentId: "oam.fetcher.local", tokenSymbol: "BMF-TKN" },
  { agentId: "oam.synthesizer.local", tokenSymbol: "CAV4-TKN" },
  { agentId: "oam.transformer.local", tokenSymbol: "DN-TKN" },
];

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.20",
  networks: {
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
    },
    hardhat: {
      chainId: 31337,
    },
  },
  paths: {
    sources: "./contracts",
  },
};
