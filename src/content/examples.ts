import type { AssignmentExample } from "@/types/content";

/**
 * Three sample submissions, from weak to strong. Each pairs a task with a solution and the
 * author's own explanation, exactly what a student submits. Their static results are recorded
 * from the real engine into exampleReports.generated.json (`npm run fixtures`).
 */
export const ASSIGNMENT_EXAMPLES: readonly AssignmentExample[] = [
  {
    id: "pair-sums",
    label: "Pair sums · Python",
    fileName: "pair_sums.py",
    language: "python",
    task: "Write a function `find_pairs(numbers, target)` that returns every unique pair of numbers from the list whose sum equals `target`. Return each pair once, as a tuple with the smaller number first, and sort the result.",
    explanation:
      "I go through the list with two loops and check every two numbers. If they add up to 10 I add them to the result, unless the same pair is already there in the other order.",
    code: `def f(l, r=[]):
    for i in range(len(l)):
        for j in range(len(l)):
            if i != j:
                if l[i] + l[j] == 10:
                    if [l[j], l[i]] not in r:
                        r.append([l[i], l[j]])
    return r


print(f([1, 9, 2, 8, 5, 5]))
`,
  },
  {
    id: "todo-list",
    label: "Todo list · React",
    fileName: "TodoList.jsx",
    language: "jsx",
    task: "Build a `TodoList` React component. The user can type a task and add it with a button, mark a task as done by clicking it (done tasks are crossed out), and see how many tasks are still left to do.",
    explanation:
      "The component keeps the tasks and the input text in state. Adding creates a task with a unique id from Date.now() and clears the input. Clicking a task toggles its done flag, and done tasks get a line-through style.",
    code: `import { useState } from "react";

export default function TodoList() {
  const [a, setA] = useState([]);
  const [b, setB] = useState("");

  function add() {
    setA([...a, { id: Date.now(), text: b, done: false }]);
    setB("");
  }

  function toggle(id) {
    setA(a.map((task) => (task.id === id ? { ...task, done: !task.done } : task)));
  }

  return (
    <div>
      <input value={b} onChange={(e) => setB(e.target.value)} />
      <button type="button" onClick={add}>Add</button>
      <ul>
        {a.map((task) => (
          <li key={task.id} onClick={() => toggle(task.id)} className={task.done ? "done" : ""}>
            {task.text}
          </li>
        ))}
      </ul>
    </div>
  );
}
`,
  },
  {
    id: "user-list",
    label: "User list · TypeScript",
    fileName: "UserList.tsx",
    language: "tsx",
    task: "Create a typed React component `UserList` that shows each user's avatar and name, calls `onSelect` with the user when one is chosen, and shows an empty-state message when there are no users. It must work with the keyboard.",
    explanation:
      "UserList receives a readonly array of users and an onSelect callback, both typed with interfaces. If the list is empty it returns early with an empty-state paragraph. Otherwise each user is a list item keyed by id; the name is a real button, so Tab and Enter work, and the avatar has an empty alt because the name is shown next to it.",
    code: `import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";

interface User {
  id: string;
  name: string;
  avatarUrl: string;
}

interface UserListProps {
  users: readonly User[];
  onSelect: (user: User) => void;
}

/** Lists users with their avatar; choosing one calls \`onSelect\`. Shows a message when empty. */
export function UserList({ users, onSelect }: UserListProps) {
  if (users.length === 0) {
    return <p className="empty-state">No users yet.</p>;
  }

  return (
    <ul className="user-list">
      {users.map((user) => (
        <li key={user.id}>
          <img src={user.avatarUrl} alt="" width={32} height={32} />
          <button type="button" onClick={() => onSelect(user)}>
            {user.name}
          </button>
        </li>
      ))}
    </ul>
  );
}

const ADA: User = { id: "1", name: "Ada", avatarUrl: "/ada.png" };

it("shows a message when there are no users", () => {
  render(<UserList users={[]} onSelect={vi.fn()} />);
  expect(screen.getByText("No users yet.")).toBeVisible();
});

it("reports the user that was chosen", async () => {
  const onSelect = vi.fn();
  render(<UserList users={[ADA]} onSelect={onSelect} />);
  await userEvent.click(screen.getByRole("button", { name: "Ada" }));
  expect(onSelect).toHaveBeenCalledWith(ADA);
});
`,
  },
];
