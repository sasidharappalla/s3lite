import http from "k6/http";
import { check, sleep } from "k6";

const baseUrl = __ENV.BASE_URL || "http://localhost:8001";
const apiKey = __ENV.S3LITE_API_KEY;

if (!apiKey) {
  throw new Error("S3LITE_API_KEY must be set");
}

export const options = {
  stages: [
    { duration: "30s", target: 100 },
    { duration: "2m", target: 1000 },
    { duration: "1m", target: 1000 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const health = http.get(`${baseUrl}/health`);
  check(health, {
    "health returns 200": (response) => response.status === 200,
  });

  const buckets = http.get(`${baseUrl}/buckets`, {
    headers: { "X-API-Key": apiKey },
  });
  check(buckets, {
    "bucket listing returns 200": (response) => response.status === 200,
  });

  sleep(1);
}
