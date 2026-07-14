// SPDX-License-Identifier: MIT

export interface ImageGenResult {
  url?: string;
  b64_json?: string;
  status: 'completed' | 'failed';
  error?: string;
  seed?: number;
}

export type ImageProvider = 'fal' | 'openai' | 'stability';

export interface ImageGenConfig {
  provider: ImageProvider;
  apiKey?: string;
  model?: string;
  width?: number;
  height?: number;
  numImages?: number;
}

export async function generateImage(
  prompt: string,
  config?: Partial<ImageGenConfig>,
  negativePrompt?: string,
): Promise<ImageGenResult> {
  const cfg: ImageGenConfig = {
    provider: config?.provider ?? 'openai',
    apiKey: config?.apiKey ?? process.env['OPENAI_API_KEY'] ?? process.env['FAL_KEY'],
    model: config?.model ?? 'dall-e-3',
    width: config?.width ?? 1024,
    height: config?.height ?? 1024,
    numImages: config?.numImages ?? 1,
  };

  if (!cfg.apiKey) {
    return { status: 'failed', error: 'No API key configured. Set OPENAI_API_KEY or FAL_KEY in .env' };
  }

  try {
    if (cfg.provider === 'openai') {
      return await generateOpenAI(prompt, cfg);
    }
    if (cfg.provider === 'fal') {
      return await generateFal(prompt, cfg, negativePrompt);
    }
    return { status: 'failed', error: `Unsupported provider: ${cfg.provider}` };
  } catch (e: any) {
    return { status: 'failed', error: e.message };
  }
}

async function generateOpenAI(prompt: string, cfg: ImageGenConfig): Promise<ImageGenResult> {
  const res = await fetch('https://api.openai.com/v1/images/generations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${cfg.apiKey}` },
    body: JSON.stringify({
      model: cfg.model,
      prompt,
      n: cfg.numImages,
      size: `${cfg.width}x${cfg.height}`,
      response_format: 'b64_json',
    }),
  });
  if (!res.ok) throw new Error(`OpenAI Image error ${res.status}: ${await res.text()}`);
  const data = await res.json() as any;
  return { b64_json: data.data?.[0]?.b64_json, status: 'completed', seed: data.data?.[0]?.seed };
}

async function generateFal(prompt: string, cfg: ImageGenConfig, negativePrompt?: string): Promise<ImageGenResult> {
  const res = await fetch('https://fal.run/fal-ai/flux-pro/v1.1', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Key ${cfg.apiKey}`,
    },
    body: JSON.stringify({
      prompt,
      negative_prompt: negativePrompt ?? '',
      image_size: { width: cfg.width, height: cfg.height },
      num_images: cfg.numImages,
    }),
  });
  if (!res.ok) throw new Error(`FAL error ${res.status}: ${await res.text()}`);
  const data = await res.json() as any;
  return { url: data.images?.[0]?.url, status: 'completed', seed: data.seed };
}
