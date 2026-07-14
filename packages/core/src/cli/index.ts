#!/usr/bin/env node
// SPDX-License-Identifier: MIT

import { Command } from 'commander';
import { VERSION } from '../index.js';
import { serveCommand } from './serve.js';
import { workflowCommand } from './workflow.js';
import { configCommand } from './config.js';

const program = new Command();

program
  .name('hermes')
  .description('Hermes Agent OS — 多智能体团队协作开发系统')
  .version(VERSION);

program
  .command('serve')
  .description('启动后端 API 服务器')
  .option('-p, --port <port>', '端口号', '3000')
  .option('-h, --host <host>', '监听地址', '0.0.0.0')
  .action(serveCommand);

program
  .command('workflow')
  .description('执行工作流')
  .argument('<workflow-id>', '工作流 ID')
  .option('-c, --context <json>', '初始上下文 (JSON 字符串)')
  .action(workflowCommand);

program
  .command('config')
  .description('管理配置')
  .option('-g, --get <key>', '获取配置项')
  .option('-s, --set <key> <value>', '设置配置项')
  .option('-l, --list', '列出全部配置')
  .action(configCommand);

program.parse(process.argv);
