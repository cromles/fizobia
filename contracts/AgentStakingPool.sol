// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/// @dev Ajan başına USDC staking havuzu — 1 USDC = 1 pay (6 ondalık).
contract AgentStakingPool {
    IERC20 public immutable usdc;
    string public agentId;
    string public tokenSymbol;

    uint256 public totalShares;
    uint256 private constant ACC_PRECISION = 1e12;

    uint256 public accRewardPerShare;

    struct UserInfo {
        uint256 shares;
        uint256 rewardDebt;
    }

    mapping(address => UserInfo) public users;

    event Staked(address indexed user, uint256 amount, uint256 shares);
    event Unstaked(address indexed user, uint256 shares, uint256 amount);
    event RewardClaimed(address indexed user, uint256 amount);
    event RewardsFunded(uint256 amount);

    constructor(address _usdc, string memory _agentId, string memory _tokenSymbol) {
        usdc = IERC20(_usdc);
        agentId = _agentId;
        tokenSymbol = _tokenSymbol;
    }

    function stake(uint256 amount) external {
        require(amount > 0, "zero amount");
        _harvest(msg.sender);

        require(usdc.transferFrom(msg.sender, address(this), amount), "transfer failed");

        users[msg.sender].shares += amount;
        users[msg.sender].rewardDebt = (users[msg.sender].shares * accRewardPerShare) / ACC_PRECISION;
        totalShares += amount;

        emit Staked(msg.sender, amount, amount);
    }

    function unstake(uint256 shareAmount) external {
        require(shareAmount > 0, "zero shares");
        UserInfo storage user = users[msg.sender];
        require(user.shares >= shareAmount, "insufficient shares");
        _harvest(msg.sender);

        user.shares -= shareAmount;
        totalShares -= shareAmount;
        user.rewardDebt = (user.shares * accRewardPerShare) / ACC_PRECISION;

        require(usdc.transfer(msg.sender, shareAmount), "transfer failed");
        emit Unstaked(msg.sender, shareAmount, shareAmount);
    }

    function fundRewards(uint256 amount) external {
        require(amount > 0, "zero reward");
        require(usdc.transferFrom(msg.sender, address(this), amount), "reward transfer failed");
        if (totalShares == 0) {
            return;
        }
        accRewardPerShare += (amount * ACC_PRECISION) / totalShares;
        emit RewardsFunded(amount);
    }

    function pendingReward(address userAddr) public view returns (uint256) {
        UserInfo storage user = users[userAddr];
        return (user.shares * accRewardPerShare) / ACC_PRECISION - user.rewardDebt;
    }

    function claimRewards() external {
        _harvest(msg.sender);
    }

    function _harvest(address userAddr) internal {
        uint256 pending = pendingReward(userAddr);
        if (pending == 0) {
            return;
        }
        users[userAddr].rewardDebt = (users[userAddr].shares * accRewardPerShare) / ACC_PRECISION;
        require(usdc.transfer(userAddr, pending), "reward payout failed");
        emit RewardClaimed(userAddr, pending);
    }
}
