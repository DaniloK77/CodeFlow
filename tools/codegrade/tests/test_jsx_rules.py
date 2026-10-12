"""React and accessibility rules: each fires on bad JSX and not on its fix."""

from __future__ import annotations

import pytest

from .helpers import rules_in

CASES = [
    ("img-alt", "const view = <img src={src} />;", 'const view = <img src={src} alt="Logo" />;'),
    (
        "button-type",
        "const view = <button onClick={save}>Save</button>;",
        'const view = <button type="button" onClick={save}>Save</button>;',
    ),
    (
        "placeholder-href",
        'const view = <a href="#">More</a>;',
        'const view = <a href="/more">More</a>;',
    ),
    (
        "click-non-interactive",
        "const view = <div onClick={open}>Open</div>;",
        'const view = <button type="button" onClick={open}>Open</button>;',
    ),
    (
        "click-non-interactive",
        "const view = <span onClick={open}>Open</span>;",
        'const view = <div role="button" tabIndex={0} onClick={open} onKeyDown={press}>Open</div>;',
    ),
    (
        "input-label",
        "const view = <input value={value} onChange={change} />;",
        'const view = <input aria-label="Search" value={value} onChange={change} />;',
    ),
    (
        "input-label",
        "const view = <select value={value} onChange={change} />;",
        'const view = <input type="hidden" value={value} />;',
    ),
    (
        "missing-key",
        "const rows = items.map((item) => <li>{item.name}</li>);",
        "const rows = items.map((item) => <li key={item.id}>{item.name}</li>);",
    ),
    (
        "index-as-key",
        "const rows = items.map((item, index) => <li key={index}>{item.name}</li>);",
        "const rows = items.map((item) => <li key={item.id}>{item.name}</li>);",
    ),
    (
        "effect-cleanup",
        'useEffect(() => { window.addEventListener("resize", onResize); }, []);',
        """
        useEffect(() => {
          window.addEventListener("resize", onResize);
          return () => window.removeEventListener("resize", onResize);
        }, []);
        """,
    ),
    (
        "effect-cleanup",
        "useEffect(() => { setInterval(tick, 1000); }, []);",
        """
        useEffect(() => {
          const id = setInterval(tick, 1000);
          return () => clearInterval(id);
        }, []);
        """,
    ),
    (
        "effect-race",
        "useEffect(() => { fetch(url).then(read).then(setData).catch(report); }, [url]);",
        """
        useEffect(() => {
          const controller = new AbortController();
          fetch(url, { signal: controller.signal }).then(read).then(setData).catch(report);
          return () => controller.abort();
        }, [url]);
        """,
    ),
    (
        "state-mutation",
        "const [items, setItems] = useState([]);\nitems.push(item);",
        "const [items, setItems] = useState([]);\nsetItems([...items, item]);",
    ),
    (
        "state-mutation",
        "const [user, setUser] = useState(initial);\nuser.name = name;",
        "const [user, setUser] = useState(initial);\nsetUser({ ...user, name });",
    ),
]


@pytest.mark.parametrize(("rule", "bad", "good"), CASES)
def test_rule_fires_on_the_problem_and_not_on_the_fix(rule: str, bad: str, good: str) -> None:
    assert rule in rules_in(bad)
    assert rule not in rules_in(good)


def test_a_label_wrapping_the_field_labels_it() -> None:
    code = "const view = <label>Email <input value={value} onChange={change} /></label>;"
    assert "input-label" not in rules_in(code)


def test_only_the_root_element_of_a_list_item_needs_a_key() -> None:
    code = """
        const rows = items.map((item) => (
          <li key={item.id}><span>{item.name}</span></li>
        ));
    """
    assert "missing-key" not in rules_in(code)


def test_submit_buttons_are_typed() -> None:
    assert "button-type" not in rules_in('const view = <button type="submit">Send</button>;')


def test_jsx_inside_an_object_built_by_map_is_not_a_list_item() -> None:
    code = """
        const items = modes.map(({ id, label }) => ({ id, label: <>{label}</> }));
    """
    assert "missing-key" not in rules_in(code)


def test_a_conditionally_returned_item_still_needs_a_key() -> None:
    code = "const rows = items.map((item) => (item.visible ? <li>{item.name}</li> : null));"
    assert "missing-key" in rules_in(code)
