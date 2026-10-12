import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import archiveReport from "./fixtures/archive-homework.json";
import health from "./fixtures/health.json";
import pairSumsQuality from "./fixtures/quality-pair-sums.json";
import todoListQuality from "./fixtures/quality-todo-list.json";
import userListQuality from "./fixtures/quality-user-list.json";
import rejectedNotCode from "./fixtures/rejected-not-code.json";
import todoListReview from "./fixtures/review-todo-list.json";

// Recorded by `npm run fixtures` from the real API code: static analysis is real, and the one
// AI review (review-todo-list) is a fixed stand-in, so the tests never call Claude.
export const fixtures = {
  archiveReport,
  health,
  pairSumsQuality,
  todoListQuality,
  userListQuality,
  todoListReview,
  rejectedNotCode,
};

export const handlers = [
  http.get("*/api/health", () => HttpResponse.json(health)),
  http.post("*/api/review/snippet", async ({ request }) => {
    const { code } = (await request.json()) as { code: string };
    if (code.includes("def f(l")) return HttpResponse.json(pairSumsQuality);
    if (code.includes("TodoList")) return HttpResponse.json(todoListReview);
    return HttpResponse.json(userListQuality);
  }),
  http.post("*/api/review/archive", () => HttpResponse.json(archiveReport)),
];

export const server = setupServer(...handlers);
