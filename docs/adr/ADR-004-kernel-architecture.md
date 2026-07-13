# ADR-004: Kernel 架构设计

## 上下文
HEP-006 Kernel 是 Hermes Agent OS 的核心运行时，负责 Agent 生命周期管理、进程调度、事件分发、插件加载。

## 决策
采用 **事件驱动 (Event-Driven) + Worker Threads** 架构。

### 进程模型对比
| 方案 | 内存 | 隔离度 | 性能 | 推荐场景 |
|------|------|--------|------|----------|
| **child_process** | 独立 | 高 | 中 | 需要强隔离的插件 |
| **worker_threads** | 共享 | 中 | 高 | CPU 密集任务、Agent 运行时 |
| **cluster** | 独立 | 高 | 中高 | HTTP 服务负载均衡 |

### 决策理由
- **Event-Driven**: 适合 Agent 间消息传递、状态变更通知
- **Worker Threads**: Agent 执行引擎需要并行计算，共享内存效率高
- **child_process** 给不可信插件（Plugin SDK）隔离

### 整体架构
```
Kernel
├── EventBus (核心事件总线)
│   ├── Agent lifecycle events
│   ├── Workflow events
│   ├── Model response events
│   └── System events
├── AgentManager (主线程)
│   ├── Agent 注册/销毁
│   ├── 状态管理
│   └── 调度策略 (Round-Robin / Priority)
├── PluginLoader (隔离进程)
│   └── 第三方插件沙箱 (child_process + IPC)
├── Scheduler (定时任务)
└── CheckpointManager (检查点/恢复)
```

## 后果
- ✅ 事件驱动解耦各模块
- ✅ Worker 线程处理 AI 推理调用不阻塞主线程
- ⚠️ 共享内存需要仔细的锁/原子操作
- ⚠️ Worker Threads 调试复杂度较高

## 状态
ACCEPTED
