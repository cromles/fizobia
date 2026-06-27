from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from eth_abi import decode, encode as abi_encode
from eth_utils import keccak, to_checksum_address

from app.config import settings

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = ROOT / "artifacts" / "contracts"

STAKED_TOPIC = keccak(text="Staked(address,uint256,uint256)").hex()
UNSTAKED_TOPIC = keccak(text="Unstaked(address,uint256,uint256)").hex()
CLAIMED_TOPIC = keccak(text="RewardClaimed(address,uint256)").hex()

_CHAIN_UI_META: Dict[int, Dict[str, Any]] = {
    31337: {
        "chain_name": "OAM Local",
        "rpc_urls": ["http://127.0.0.1:8545"],
        "block_explorer_urls": [],
    },
    84532: {
        "chain_name": "Base Sepolia",
        "rpc_urls": ["https://sepolia.base.org"],
        "block_explorer_urls": ["https://sepolia.basescan.org"],
    },
}


@dataclass(frozen=True)
class OnchainDeployment:
    chain_id: int
    network: str
    rpc_url: str
    deployer: str
    usdc: str
    factory: str
    pools: Dict[str, Dict[str, str]]
    usdc_decimals: int

    def pool_address(self, agent_id: str) -> Optional[str]:
        pool = self.pools.get(agent_id)
        return pool.get("address") if pool else None


_deployment: Optional[OnchainDeployment] = None


def _load_deployment_file() -> Optional[Dict[str, Any]]:
    path = Path(settings.onchain_deployment_file)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not raw.get("usdc"):
            return None
        return raw
    except Exception as exc:
        logger.warning("On-chain deployment okunamadı: %s", exc)
        return None


def get_deployment() -> Optional[OnchainDeployment]:
    global _deployment
    if _deployment is not None:
        return _deployment
    raw = _load_deployment_file()
    if raw is None:
        return None
    pools = dict(raw.get("pools") or {})
    factory = str(raw.get("factory") or "")
    _deployment = OnchainDeployment(
        chain_id=int(raw.get("chain_id", settings.onchain_chain_id)),
        network=str(raw.get("network", "base-sepolia")),
        rpc_url=str(raw.get("rpc_url", settings.onchain_rpc_url)),
        deployer=str(raw.get("deployer", "")),
        usdc=str(raw["usdc"]),
        factory=factory,
        pools=pools,
        usdc_decimals=int(raw.get("usdc_decimals", 6)),
    )
    return _deployment


def _rpc(method: str, params: List[Any]) -> Any:
    deployment = get_deployment()
    rpc_url = deployment.rpc_url if deployment else settings.onchain_rpc_url
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    with httpx.Client(timeout=15.0) as client:
        response = client.post(rpc_url, json=payload)
        response.raise_for_status()
        body = response.json()
    if body.get("error"):
        raise ValueError(body["error"].get("message", "RPC hatası"))
    return body.get("result")


def rpc_connected() -> bool:
    try:
        _rpc("eth_blockNumber", [])
        return True
    except Exception:
        return False


def is_onchain_connected() -> bool:
    """RPC canlı — deployment olmasa da zincir izleme."""
    if not settings.onchain_enabled:
        return False
    return rpc_connected()


def is_onchain_ready() -> bool:
    if not settings.onchain_enabled:
        return False
    if get_deployment() is None:
        return False
    dep = get_deployment()
    if not dep or not dep.factory or not dep.pools:
        return is_onchain_connected()
    return rpc_connected()


def usdc_to_wei(amount_usdc: float) -> int:
    deployment = get_deployment()
    decimals = deployment.usdc_decimals if deployment else 6
    return int(round(amount_usdc * (10**decimals)))


def wei_to_usdc(amount_wei: int) -> float:
    deployment = get_deployment()
    decimals = deployment.usdc_decimals if deployment else 6
    return amount_wei / (10**decimals)


def _checksum(address: str) -> str:
    return to_checksum_address(address)


def _topic_hex(value: str) -> str:
    if value.startswith("0x"):
        return value.lower()
    return f"0x{value.lower()}"


def _address_from_topic(topic: str) -> str:
    return _checksum("0x" + topic[-40:])


def get_deployer_address() -> Optional[str]:
    deployment = get_deployment()
    if deployment and deployment.deployer:
        return deployment.deployer
    payee = settings.x402_payee_address.strip()
    return payee or None


def get_deployer_balance_eth() -> Optional[float]:
    addr = get_deployer_address()
    if not addr:
        return None
    try:
        rpc_url = settings.onchain_rpc_url if settings.onchain_enabled else settings.x402_rpc_url
        payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance", "params": [addr, "latest"]}
        with httpx.Client(timeout=10.0) as client:
            response = client.post(rpc_url, json=payload)
            response.raise_for_status()
            body = response.json()
        wei = int(body["result"], 16)
        return round(wei / 1e18, 6)
    except Exception:
        return None


def build_public_config() -> Dict[str, Any]:
    deployment = get_deployment()
    connected = is_onchain_connected()
    ready = is_onchain_ready()
    chain_id = deployment.chain_id if deployment else settings.onchain_chain_id
    ui_meta = dict(_CHAIN_UI_META.get(chain_id, {}))
    if deployment and deployment.rpc_url and "rpc_urls" not in ui_meta:
        ui_meta["rpc_urls"] = [deployment.rpc_url]
    elif settings.onchain_rpc_url:
        ui_meta.setdefault("rpc_urls", [settings.onchain_rpc_url])
    if deployment and deployment.network and "chain_name" not in ui_meta:
        ui_meta["chain_name"] = deployment.network.replace("-", " ").title()
    pools = deployment.pools if deployment else {}
    has_pools = bool(pools)
    if ready and has_pools and deployment and deployment.factory:
        stake_mode = "onchain"
    else:
        stake_mode = "ledger_demo"

    deployer = get_deployer_address()
    deployer_balance = get_deployer_balance_eth()

    return {
        "enabled": settings.onchain_enabled,
        "connected": connected,
        "ready": ready,
        "stake_mode": stake_mode,
        "deployer": deployer,
        "deployer_balance_eth": deployer_balance,
        "deploy_ready": bool(deployer_balance and deployer_balance > 0),
        "chain_id": chain_id,
        "network": deployment.network if deployment else settings.x402_network,
        "chain_name": ui_meta.get("chain_name", "Base Sepolia"),
        "rpc_urls": ui_meta.get("rpc_urls", [settings.onchain_rpc_url]),
        "block_explorer_urls": ui_meta.get("block_explorer_urls", ["https://sepolia.basescan.org"]),
        "usdc": deployment.usdc if deployment and deployment.usdc else settings.x402_usdc_contract,
        "factory": deployment.factory if deployment else None,
        "pools": pools,
        "pool_count": len(pools),
        "usdc_decimals": deployment.usdc_decimals if deployment else 6,
        "require_tx": settings.onchain_require_tx and ready and stake_mode == "onchain",
        "wallet_mode": "metamask",
    }


def apply_pool_addresses(hub: Any) -> None:
    deployment = get_deployment()
    if deployment is None:
        return
    for agent_id, meta in deployment.pools.items():
        pool = hub.pools.get_pool(agent_id)
        address = meta.get("address")
        if pool is not None and address:
            pool.contract_address = address
        elif address:
            symbol = meta.get("token_symbol", "TKN")
            created = hub.pools.ensure_pool(agent_id, symbol)
            created.contract_address = address


def _wait_for_receipt(tx_hash: str, timeout: float = 60.0) -> Dict[str, Any]:
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        receipt = _rpc("eth_getTransactionReceipt", [tx_hash])
        if receipt is not None:
            return receipt
        time.sleep(0.4)
    raise ValueError("İşlem onayı zaman aşımı")


def verify_stake_tx(
    tx_hash: str,
    investor_id: str,
    agent_id: str,
    amount_usdc: float,
) -> Dict[str, Any]:
    deployment = get_deployment()
    if deployment is None:
        raise ValueError("On-chain deployment bulunamadı")

    pool_address = deployment.pool_address(agent_id)
    if not pool_address:
        raise ValueError(f"On-chain havuz yok: {agent_id}")

    receipt = _wait_for_receipt(tx_hash)
    if int(receipt.get("status", "0x0"), 16) != 1:
        raise ValueError("İşlem başarısız (reverted)")

    expected_amount = usdc_to_wei(amount_usdc)
    investor = _checksum(investor_id)
    pool_lower = pool_address.lower()

    for log in receipt.get("logs", []):
        if log.get("address", "").lower() != pool_lower:
            continue
        topics = [_topic_hex(t) for t in log.get("topics", [])]
        if not topics or topics[0] != _topic_hex(STAKED_TOPIC):
            continue
        if len(topics) < 2:
            continue
        logged_user = _address_from_topic(topics[1])
        if logged_user.lower() != investor.lower():
            continue
        data_hex = log.get("data", "0x")
        if data_hex.startswith("0x"):
            data_hex = data_hex[2:]
        amount, shares = decode(["uint256", "uint256"], bytes.fromhex(data_hex))
        if abs(amount - expected_amount) > 1:
            raise ValueError("Stake miktarı zincir ile uyuşmuyor")
        return {
            "tx_hash": tx_hash,
            "investor": investor,
            "agent_id": agent_id,
            "amount_wei": amount,
            "shares_wei": shares,
            "pool": pool_address,
        }

    raise ValueError("Stake event bulunamadı")


def verify_unstake_tx(
    tx_hash: str,
    investor_id: str,
    agent_id: str,
    shares: float,
) -> Dict[str, Any]:
    deployment = get_deployment()
    if deployment is None:
        raise ValueError("On-chain deployment bulunamadı")

    pool_address = deployment.pool_address(agent_id)
    if not pool_address:
        raise ValueError(f"On-chain havuz yok: {agent_id}")

    receipt = _wait_for_receipt(tx_hash)
    if int(receipt.get("status", "0x0"), 16) != 1:
        raise ValueError("Unstake işlemi başarısız")

    expected_shares = usdc_to_wei(shares)
    investor = _checksum(investor_id)
    pool_lower = pool_address.lower()

    for log in receipt.get("logs", []):
        if log.get("address", "").lower() != pool_lower:
            continue
        topics = [_topic_hex(t) for t in log.get("topics", [])]
        if not topics or topics[0] != _topic_hex(UNSTAKED_TOPIC):
            continue
        if len(topics) < 2:
            continue
        logged_user = _address_from_topic(topics[1])
        if logged_user.lower() != investor.lower():
            continue
        data_hex = log.get("data", "0x")
        if data_hex.startswith("0x"):
            data_hex = data_hex[2:]
        logged_shares, amount = decode(["uint256", "uint256"], bytes.fromhex(data_hex))
        if abs(logged_shares - expected_shares) > 1:
            raise ValueError("Unstake pay miktarı zincir ile uyuşmuyor")
        if abs(amount - expected_shares) > 1:
            raise ValueError("Unstake USDC miktarı zincir ile uyuşmuyor")
        return {
            "tx_hash": tx_hash,
            "investor": investor,
            "agent_id": agent_id,
            "shares_wei": logged_shares,
            "usdc_returned": wei_to_usdc(amount),
            "pool": pool_address,
        }

    raise ValueError("Unstaked event bulunamadı")


def verify_claim_tx(tx_hash: str, investor_id: str, agent_id: str) -> Dict[str, Any]:
    deployment = get_deployment()
    if deployment is None:
        raise ValueError("On-chain deployment bulunamadı")

    pool_address = deployment.pool_address(agent_id)
    if not pool_address:
        raise ValueError(f"On-chain havuz yok: {agent_id}")

    receipt = _wait_for_receipt(tx_hash)
    if int(receipt.get("status", "0x0"), 16) != 1:
        raise ValueError("Claim işlemi başarısız")

    investor = _checksum(investor_id)
    pool_lower = pool_address.lower()
    claimed_wei = 0

    for log in receipt.get("logs", []):
        if log.get("address", "").lower() != pool_lower:
            continue
        topics = [_topic_hex(t) for t in log.get("topics", [])]
        if not topics or topics[0] != _topic_hex(CLAIMED_TOPIC):
            continue
        logged_user = _address_from_topic(topics[1])
        if logged_user.lower() != investor.lower():
            continue
        data_hex = log.get("data", "0x")[2:]
        (claimed_wei,) = decode(["uint256"], bytes.fromhex(data_hex))
        break

    if claimed_wei <= 0:
        raise ValueError("RewardClaimed event bulunamadı")

    return {
        "tx_hash": tx_hash,
        "claimed_usdc": wei_to_usdc(claimed_wei),
        "agent_id": agent_id,
    }


def fund_pool_rewards(agent_id: str, amount_usdc: float) -> Optional[str]:
    """Operatör cüzdanı ile staking havuzuna on-chain ödül yatırır."""
    if amount_usdc <= 0 or not settings.onchain_operator_key:
        return None
    deployment = get_deployment()
    if deployment is None or not rpc_connected():
        return None

    pool_address = deployment.pool_address(agent_id)
    if not pool_address:
        return None

    try:
        from eth_account import Account
    except ImportError:
        logger.warning("eth-account yüklü değil — on-chain ödül atlandı")
        return None

    amount_wei = usdc_to_wei(amount_usdc)
    if amount_wei <= 0:
        return None

    operator = Account.from_key(settings.onchain_operator_key)
    usdc = _checksum(deployment.usdc)
    pool = _checksum(pool_address)

    approve_selector = keccak(text="approve(address,uint256)")[:4]
    fund_selector = keccak(text="fundRewards(uint256)")[:4]

    nonce = int(_rpc("eth_getTransactionCount", [operator.address, "latest"]), 16)
    chain_id = deployment.chain_id

    approve_data = "0x" + (approve_selector + abi_encode(["address", "uint256"], [pool, amount_wei]).hex())
    approve_tx = {
        "to": usdc,
        "from": operator.address,
        "data": approve_data,
        "nonce": nonce,
        "chainId": chain_id,
        "gas": 120_000,
        "gasPrice": int(_rpc("eth_gasPrice", []), 16),
        "value": 0,
    }
    signed = operator.sign_transaction(approve_tx)
    tx_hash = _rpc("eth_sendRawTransaction", [signed.raw_transaction.hex()])
    _wait_for_receipt(tx_hash)

    fund_data = "0x" + (fund_selector + abi_encode(["uint256"], [amount_wei]).hex())
    fund_tx = {
        "to": pool,
        "from": operator.address,
        "data": fund_data,
        "nonce": nonce + 1,
        "chainId": chain_id,
        "gas": 200_000,
        "gasPrice": int(_rpc("eth_gasPrice", []), 16),
        "value": 0,
    }
    signed_fund = operator.sign_transaction(fund_tx)
    fund_hash = _rpc("eth_sendRawTransaction", [signed_fund.raw_transaction.hex()])
    receipt = _wait_for_receipt(fund_hash)
    if int(receipt.get("status", "0x0"), 16) != 1:
        logger.warning("fundRewards başarısız: %s", fund_hash)
        return None
    return fund_hash
