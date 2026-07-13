// SPDX-License-Identifier: MIT

type TaskFn = () => Promise<void>;

interface Task {
  id: string;
  fn: TaskFn;
  interval: number;
  type: 'interval' | 'timeout';
  lastRun: number;
  timer: ReturnType<typeof setInterval> | ReturnType<typeof setTimeout> | null;
}

export class Scheduler {
  private tasks: Map<string, Task> = new Map();
  private running = false;

  start(): void {
    this.running = true;
  }

  stop(): void {
    this.running = false;
    for (const task of Array.from(this.tasks.values())) {
      this._clearTimer(task);
    }
    this.tasks.clear();
  }

  schedule(id: string, fn: TaskFn, intervalMs: number): void {
    if (this.tasks.has(id)) {
      this._clearTimer(this.tasks.get(id)!);
    }

    const task: Task = {
      id,
      fn,
      interval: intervalMs,
      type: 'interval',
      lastRun: 0,
      timer: null,
    };

    task.timer = setInterval(async () => {
      if (!this.running) return;
      try {
        task.lastRun = Date.now();
        await fn();
      } catch {
        // task error swallowed — scheduler continues
      }
    }, intervalMs);

    this.tasks.set(id, task);
  }

  scheduleOnce(id: string, fn: TaskFn, delayMs: number): void {
    const task: Task = {
      id,
      fn,
      interval: delayMs,
      type: 'timeout',
      lastRun: 0,
      timer: null,
    };

    task.timer = setTimeout(async () => {
      this.tasks.delete(id);
      try {
        task.lastRun = Date.now();
        await fn();
      } catch {
        // task error swallowed
      }
    }, delayMs);

    this.tasks.set(id, task);
  }

  cancel(id: string): boolean {
    const task = this.tasks.get(id);
    if (!task) return false;
    this._clearTimer(task);
    this.tasks.delete(id);
    return true;
  }

  has(id: string): boolean {
    return this.tasks.has(id);
  }

  list(): { id: string; type: string; interval: number; lastRun: number }[] {
    return Array.from(this.tasks.values()).map(t => ({
      id: t.id,
      type: t.type,
      interval: t.interval,
      lastRun: t.lastRun,
    }));
  }

  private _clearTimer(task: Task): void {
    if (task.timer) {
      if (task.type === 'interval') {
        clearInterval(task.timer as ReturnType<typeof setInterval>);
      } else {
        clearTimeout(task.timer as ReturnType<typeof setTimeout>);
      }
      task.timer = null;
    }
  }
}
