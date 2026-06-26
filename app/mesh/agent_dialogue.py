from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

_dialogue: Optional["AgentDialogueBus"] = None


@dataclass
class AgentMessage:
    message_id: str
    thread_id: str
    from_agent: str
    to_agent: str
    intent: str
    text: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_public(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "from": self.from_agent,
            "to": self.to_agent,
            "intent": self.intent,
            "text": self.text,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class AgentDialogueBus:
    """Ajanlar arası mesajlaşma — mesh içi konuşma günlüğü."""

    def __init__(self, max_messages: int = 500) -> None:
        self.messages: Deque[AgentMessage] = deque(maxlen=max_messages)
        self._threads: Dict[str, List[str]] = {}

    def say(
        self,
        from_agent: str,
        to_agent: str,
        text: str,
        *,
        intent: str = "inform",
        payload: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
    ) -> AgentMessage:
        tid = thread_id or f"thread_{uuid.uuid4().hex[:10]}"
        msg = AgentMessage(
            message_id=f"msg_{uuid.uuid4().hex[:10]}",
            thread_id=tid,
            from_agent=from_agent,
            to_agent=to_agent,
            intent=intent,
            text=text,
            payload=payload or {},
        )
        self.messages.appendleft(msg)
        self._threads.setdefault(tid, []).append(msg.message_id)
        return msg

    def broadcast(
        self,
        from_agent: str,
        text: str,
        *,
        intent: str = "broadcast",
        payload: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
    ) -> AgentMessage:
        return self.say(
            from_agent,
            "*",
            text,
            intent=intent,
            payload=payload,
            thread_id=thread_id,
        )

    def reply(
        self,
        prior: AgentMessage,
        from_agent: str,
        text: str,
        *,
        intent: str = "response",
        payload: Optional[Dict[str, Any]] = None,
    ) -> AgentMessage:
        return self.say(
            from_agent,
            prior.from_agent if prior.to_agent == from_agent else prior.to_agent,
            text,
            intent=intent,
            payload=payload,
            thread_id=prior.thread_id,
        )

    def list_messages(
        self,
        *,
        limit: int = 50,
        thread_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        items = list(self.messages)
        if thread_id:
            items = [m for m in items if m.thread_id == thread_id]
        if agent_id:
            items = [
                m
                for m in items
                if m.from_agent == agent_id
                or m.to_agent == agent_id
                or m.to_agent == "*"
            ]
        return [m.to_public() for m in items[:limit]]

    def thread_summary(self, thread_id: str) -> Dict[str, Any]:
        msgs = [m for m in self.messages if m.thread_id == thread_id]
        return {
            "thread_id": thread_id,
            "message_count": len(msgs),
            "participants": sorted(
                {m.from_agent for m in msgs} | {m.to_agent for m in msgs if m.to_agent != "*"}
            ),
            "messages": [m.to_public() for m in reversed(msgs)],
        }


def get_dialogue_bus() -> AgentDialogueBus:
    global _dialogue
    if _dialogue is None:
        _dialogue = AgentDialogueBus()
    return _dialogue


def reset_dialogue_bus() -> None:
    global _dialogue
    _dialogue = AgentDialogueBus()
