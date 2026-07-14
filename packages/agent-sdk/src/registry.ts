// SPDX-License-Identifier: MIT

import { Agent } from './agent.js';
import type { AgentCapability } from './types.js';

export class AgentRegistry {
  private agents: Map<string, Agent> = new Map();
  private capabilityIndex: Map<string, Set<string>> = new Map();

  register(agent: Agent): void {
    this.agents.set(agent.id, agent);
    for (const cap of agent.capabilities) {
      const ids = this.capabilityIndex.get(cap.name) ?? new Set();
      ids.add(agent.id);
      this.capabilityIndex.set(cap.name, ids);
    }
  }

  unregister(agentId: string): boolean {
    const agent = this.agents.get(agentId);
    if (!agent) return false;
    for (const cap of agent.capabilities) {
      this.capabilityIndex.get(cap.name)?.delete(agentId);
    }
    this.agents.delete(agentId);
    return true;
  }

  getAgent(id: string): Agent | undefined {
    return this.agents.get(id);
  }

  findAgentsByCapability(capability: string): Agent[] {
    const ids = this.capabilityIndex.get(capability);
    if (!ids) return [];
    return Array.from(ids).map(id => this.agents.get(id)).filter(Boolean) as Agent[];
  }

  listAgents(): Agent[] {
    return Array.from(this.agents.values());
  }

  count(): number {
    return this.agents.size;
  }

  hasAgent(id: string): boolean {
    return this.agents.has(id);
  }
}
