#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from textwrap import dedent


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[’'`]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "hugo.toml").exists() and (cwd / "content").exists():
        return cwd

    for parent in cwd.parents:
        if (parent / "hugo.toml").exists() and (parent / "content").exists():
            return parent

    raise SystemExit(
        "Run this from your Hugo repo root (the folder containing hugo.toml and content/)."
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def open_in_editor(path: Path) -> None:
    editor = os.environ.get("EDITOR", "").strip()

    if editor:
        cmd = shlex.split(editor) + [str(path)]
        subprocess.run(cmd, check=False)
        return

    if shutil.which("code"):
        subprocess.run(["code", "--wait", str(path)], check=False)
        return

    if sys.platform == "darwin":
        subprocess.run(["open", "-e", str(path)], check=False)
        return

    if shutil.which("nano"):
        subprocess.run(["nano", str(path)], check=False)
        return

    print(f"Created file: {path}")
    print("No editor found. Set the EDITOR environment variable to open files automatically.")


def list_sections(content_root: Path) -> list[Path]:
    sections = []
    for p in content_root.iterdir():
        if p.is_dir() and not p.name.startswith("."):
            sections.append(p)
    return sorted(sections, key=lambda p: p.name.lower())


def prompt(msg: str, default: str | None = None) -> str:
    if default:
        raw = input(f"{msg} [{default}]: ").strip()
        return raw or default
    return input(f"{msg}: ").strip()


def prompt_bool(msg: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    raw = input(f"{msg} ({hint}): ").strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes", "true", "1"}


def choose_from_list(items: list[str], title: str) -> int:
    print(f"\n{title}")
    for i, item in enumerate(items, 1):
        print(f"  {i}) {item}")

    while True:
        choice = input("Choose a number: ").strip()
        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= len(items):
                return n - 1
        print("Please enter a valid number.")


def section_title_from_name(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").title()


def ensure_menu_entry(hugo_toml: Path, section: str, title: str) -> None:
    text = read_text(hugo_toml)
    page_ref = f'pageRef = "/{section}"'
    if page_ref in text:
        return

    weights = [int(w) for w in re.findall(r"^\s*weight\s*=\s*(\d+)\s*$", text, flags=re.M)]
    next_weight = (max(weights) + 10) if weights else 10

    entry = dedent(
        f"""
          [[menus.main]]
            name = "{title}"
            pageRef = "/{section}"
            weight = {next_weight}
        """
    ).strip("\n") + "\n"

    if "[menus]" not in text:
        # If the file has no [menus] section, add one near the top.
        # This keeps the script usable even in a very simple config.
        insert_after = re.search(r"(?m)^theme\s*=.*$", text)
        if insert_after:
            pos = insert_after.end()
            text = text[:pos] + "\n\n[menus]\n" + text[pos:]
        else:
            text = text.rstrip() + "\n\n[menus]\n"

    if "[taxonomies]" in text:
        text = text.replace("[taxonomies]", entry + "\n[taxonomies]", 1)
    else:
        text = text.rstrip() + "\n\n" + entry

    write_text(hugo_toml, text)


def create_section(root: Path, section: str, title: str | None = None, intro: str = "") -> Path:
    content_root = root / "content"
    section_dir = content_root / section
    section_dir.mkdir(parents=True, exist_ok=True)

    title = title or section_title_from_name(section)
    intro_block = intro.strip()
    body = f"""---
title: "{title}"
---

{intro_block}
"""
    write_text(section_dir / "_index.md", body)

    ensure_menu_entry(root / "hugo.toml", section, title)
    return section_dir / "_index.md"


def create_post(
    root: Path,
    section: str,
    title: str,
    slug: str | None = None,
    tags: list[str] | None = None,
    categories: list[str] | None = None,
    summary: str = "",
    draft: bool = False,
    open_after: bool = True,
) -> Path:
    content_root = root / "content"
    section_dir = content_root / section
    if not section_dir.exists():
        raise SystemExit(f"Section folder does not exist: content/{section}")

    slug = slug or slugify(title)
    post_dir = section_dir / slug
    post_dir.mkdir(parents=True, exist_ok=True)

    tags = tags or []
    categories = categories or [section]

    tag_lines = "\n".join(f'  "{t}"' for t in tags)
    cat_lines = "\n".join(f'  "{c}"' for c in categories)

    extra_summary = f'\nsummary: "{summary}"' if summary else ""

    content = dedent(
        f"""---
title: "{title}"
date: {date.today().isoformat()}
draft: {str(draft).lower()}{extra_summary}
tags:
{tag_lines if tag_lines else '  []'}
categories:
{cat_lines if cat_lines else '  []'}
---

Write your post here.

## Summary

## Main points

## My reflection

## Links

- [Source](https://example.com)

## Figures

![Figure caption](figure1.png)
"""
    )

    index_file = post_dir / "index.md"
    write_text(index_file, content)

    if open_after:
        open_in_editor(index_file)

    return index_file


def list_posts(root: Path) -> list[Path]:
    content_root = root / "content"
    posts: list[Path] = []
    for path in content_root.rglob("index.md"):
        if path.name == "index.md" and path.parent.name != "content":
            posts.append(path)
    for path in content_root.rglob("*.md"):
        if path.name == "_index.md":
            continue
        if path.name == "index.md":
            continue
        if path.parent == content_root:
            posts.append(path)
    return sorted(posts, key=lambda p: str(p).lower())


def interactive_new_section(root: Path) -> None:
    section = prompt("New tab folder name (example: concepts)")
    if not section:
        print("Cancelled.")
        return

    section = slugify(section)
    title = prompt("Tab title", section_title_from_name(section))
    intro = prompt("Short landing-page description", "")

    file_path = create_section(root, section, title=title, intro=intro)
    print(f"Created: {file_path}")
    print(f"Menu updated for tab: {title}")


def interactive_new_post(root: Path) -> None:
    content_root = root / "content"
    sections = list_sections(content_root)

    section_names = [s.name for s in sections]
    section_names.append("Create a new tab/section")

    choice = choose_from_list(section_names, "Choose where the post should go")

    if choice == len(sections):
        interactive_new_section(root)
        sections = list_sections(content_root)
        section_names = [s.name for s in sections]
        choice = choose_from_list(section_names, "Choose the tab for the post")

    section = sections[choice].name

    title = prompt("Post title")
    if not title:
        print("Cancelled.")
        return

    slug_default = slugify(title)
    slug = prompt("Slug for URL/folder", slug_default)

    tags_raw = prompt("Tags (comma-separated)", "")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    summary = prompt("Short summary (optional)", "")
    draft = prompt_bool("Mark as draft?", default=False)

    create_post(
        root=root,
        section=section,
        title=title,
        slug=slug,
        tags=tags,
        categories=[section],
        summary=summary,
        draft=draft,
        open_after=True,
    )
    print(f"Created post under /{section}/{slug}/")


def interactive_edit_existing(root: Path) -> None:
    posts = list_posts(root)
    if not posts:
        print("No markdown posts found yet.")
        return

    labels = []
    for p in posts:
        labels.append(str(p.relative_to(root)))

    choice = choose_from_list(labels, "Choose a file to open")
    open_in_editor(posts[choice])


def main() -> None:
    root = repo_root()

    parser = argparse.ArgumentParser(
        description="Helper for managing Hugo posts and tabs."
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("interactive", help="Open the menu-driven workflow")

    p_sec = sub.add_parser("new-section", help="Create a new tab/section")
    p_sec.add_argument("--section", required=True, help="Folder name, like concepts")
    p_sec.add_argument("--title", default=None, help="Display title for the tab")
    p_sec.add_argument("--intro", default="", help="Landing page text")

    p_post = sub.add_parser("new-post", help="Create a new post")
    p_post.add_argument("--section", required=True, help="Section folder name")
    p_post.add_argument("--title", required=True, help="Post title")
    p_post.add_argument("--slug", default=None, help="Folder slug for the post")
    p_post.add_argument("--tags", default="", help="Comma-separated tags")
    p_post.add_argument("--summary", default="", help="Short summary")
    p_post.add_argument("--draft", action="store_true", help="Mark as draft")
    p_post.add_argument("--no-open", action="store_true", help="Do not open in editor")

    sub.add_parser("edit", help="Choose an existing file and open it")

    args = parser.parse_args()

    if args.cmd == "new-section":
        section = slugify(args.section)
        title = args.title or section_title_from_name(section)
        path = create_section(root, section, title=title, intro=args.intro)
        print(f"Created: {path}")
        print(f"Menu updated for tab: {title}")
        return

    if args.cmd == "new-post":
        section = slugify(args.section)
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        path = create_post(
            root=root,
            section=section,
            title=args.title,
            slug=args.slug,
            tags=tags,
            categories=[section],
            summary=args.summary,
            draft=args.draft,
            open_after=not args.no_open,
        )
        print(f"Created: {path}")
        return

    if args.cmd == "edit":
        interactive_edit_existing(root)
        return

    # Default: interactive menu
    while True:
        print("\nHugo Site Tool")
        print("  1) New post")
        print("  2) New tab/section")
        print("  3) Open existing file")
        print("  4) Quit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            interactive_new_post(root)
        elif choice == "2":
            interactive_new_section(root)
        elif choice == "3":
            interactive_edit_existing(root)
        elif choice == "4":
            break
        else:
            print("Please choose 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()