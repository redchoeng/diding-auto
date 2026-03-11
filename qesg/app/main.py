"""QESG Desktop App — Flet UI for Google Workspace automation (Toss-style design)."""
import flet as ft
import json
import subprocess
import os
import threading
import shutil

from qesg.app.llm import LLMClient


# ── Auto-Update ─────────────────────────────────────────────────────────────

REPO_URL = "https://github.com/redchoeng/diding-auto.git"

def _auto_update():
    """앱 시작 시 GitHub에서 최신 코드를 pull. git 없으면 skip."""
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    git_dir = os.path.join(app_dir, ".git")

    if not os.path.isdir(git_dir):
        # git repo가 아니면 clone 시도
        git_exe = shutil.which("git")
        if not git_exe:
            return "skip"
        try:
            subprocess.run(
                [git_exe, "init"], cwd=app_dir,
                capture_output=True, text=True, timeout=10,
            )
            subprocess.run(
                [git_exe, "remote", "add", "origin", REPO_URL], cwd=app_dir,
                capture_output=True, text=True, timeout=10,
            )
            r = subprocess.run(
                [git_exe, "pull", "origin", "main", "--force"], cwd=app_dir,
                capture_output=True, text=True, timeout=60,
            )
            return "updated" if r.returncode == 0 else "error"
        except Exception:
            return "error"

    git_exe = shutil.which("git")
    if not git_exe:
        return "skip"

    try:
        r = subprocess.run(
            [git_exe, "pull", "--ff-only"], cwd=app_dir,
            capture_output=True, text=True, timeout=30,
        )
        out = r.stdout.strip()
        if "Already up to date" in out or "Already up-to-date" in out:
            return "latest"
        elif r.returncode == 0:
            return "updated"
        else:
            # ff-only 실패 시 force pull
            subprocess.run(
                [git_exe, "fetch", "origin"], cwd=app_dir,
                capture_output=True, text=True, timeout=30,
            )
            subprocess.run(
                [git_exe, "reset", "--hard", "origin/main"], cwd=app_dir,
                capture_output=True, text=True, timeout=15,
            )
            return "updated"
    except Exception:
        return "error"


# ── Toss Design Tokens ───────────────────────────────────────────────────────

class T:
    """Toss-style design tokens."""
    # Colors
    BLUE = "#3182F6"
    BLUE_LIGHT = "#E8F3FF"
    BLUE_DARK = "#1B64DA"
    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#191F28"
    TEXT_SUB = "#8B95A1"
    TEXT_CAPTION = "#B0B8C1"
    BORDER = "#E5E8EB"
    GREEN = "#00C471"
    RED = "#F04452"
    ORANGE = "#F69E36"
    GREY_50 = "#F9FAFB"
    GREY_100 = "#F2F4F6"

    # Typography
    TITLE_SIZE = 26
    HEADING_SIZE = 18
    BODY_SIZE = 14
    CAPTION_SIZE = 12

    # Spacing
    CARD_RADIUS = 16
    BTN_RADIUS = 12
    CARD_PADDING = 20
    PAGE_PADDING = 24


def toss_card(content, **kwargs):
    """Toss-style card container."""
    return ft.Container(
        content=content,
        bgcolor=T.CARD,
        border_radius=T.CARD_RADIUS,
        padding=kwargs.get("padding", T.CARD_PADDING),
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=8,
            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
        **{k: v for k, v in kwargs.items() if k != "padding"},
    )


def toss_btn(text, on_click, icon=None, primary=True):
    """Toss-style button."""
    if primary:
        return ft.Container(
            content=ft.Row(
                [ft.Icon(icon, size=16, color=T.CARD) if icon else ft.Container(width=0),
                 ft.Text(text, size=14, weight=ft.FontWeight.W_600, color=T.CARD)],
                spacing=6, alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=T.BLUE,
            border_radius=T.BTN_RADIUS,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            on_click=on_click,
            ink=True,
        )
    return ft.Container(
        content=ft.Row(
            [ft.Icon(icon, size=16, color=T.TEXT) if icon else ft.Container(width=0),
             ft.Text(text, size=14, weight=ft.FontWeight.W_500, color=T.TEXT)],
            spacing=6, alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=T.GREY_100,
        border_radius=T.BTN_RADIUS,
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        on_click=on_click,
        ink=True,
    )


def toss_input(label, **kwargs):
    """Toss-style text field."""
    return ft.TextField(
        label=label,
        border_radius=T.BTN_RADIUS,
        border_color=T.BORDER,
        focused_border_color=T.BLUE,
        label_style=ft.TextStyle(color=T.TEXT_SUB, size=13),
        text_style=ft.TextStyle(color=T.TEXT, size=14),
        cursor_color=T.BLUE,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
        **kwargs,
    )


def section_title(text, subtitle=None):
    """Section header with optional subtitle."""
    controls = [ft.Text(text, size=T.HEADING_SIZE, weight=ft.FontWeight.W_700, color=T.TEXT)]
    if subtitle:
        controls.append(ft.Text(subtitle, size=T.CAPTION_SIZE, color=T.TEXT_SUB))
    return ft.Column(controls, spacing=2)


# ── helpers ──────────────────────────────────────────────────────────────────

def _run_qesg(cmd: str) -> dict:
    """Run a qesg CLI command and return parsed JSON."""
    try:
        env = os.environ.copy()
        npm_global = os.path.join(os.environ.get("APPDATA", ""), "npm")
        env["PATH"] = npm_global + ";" + r"C:\Program Files\nodejs;" + env.get("PATH", "")

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, encoding="utf-8", env=env,
        )
        output = result.stdout.strip() or result.stderr.strip()
        try:
            return json.loads(output)
        except (json.JSONDecodeError, TypeError):
            return {"raw": output}
    except Exception as e:
        return {"error": str(e)}


def _config_path():
    return os.path.join(os.path.expanduser("~"), ".qesg", "app_config.json")


def _load_config() -> dict:
    path = _config_path()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_config(cfg: dict):
    path = _config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ── Settings Page ────────────────────────────────────────────────────────────

def _env_path():
    """Path to .env file for Google OAuth credentials."""
    return os.path.join(os.path.dirname(__file__), "..", "..", ".env")


def _load_env() -> dict:
    """Load OAuth credentials from .env file."""
    path = _env_path()
    result = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    result[k.strip()] = v.strip()
    return result


def _save_env(client_id: str, client_secret: str):
    """Save OAuth credentials to .env file."""
    path = _env_path()
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"GOOGLE_WORKSPACE_CLI_CLIENT_ID={client_id}\n")
        f.write(f"GOOGLE_WORKSPACE_CLI_CLIENT_SECRET={client_secret}\n")
    # Also set in current process environment
    os.environ["GOOGLE_WORKSPACE_CLI_CLIENT_ID"] = client_id
    os.environ["GOOGLE_WORKSPACE_CLI_CLIENT_SECRET"] = client_secret


def _check_gws_auth() -> dict:
    """Check gws installation and auth status."""
    env = os.environ.copy()
    npm_global = os.path.join(os.environ.get("APPDATA", ""), "npm")
    env["PATH"] = npm_global + ";" + r"C:\Program Files\nodejs;" + env.get("PATH", "")
    gws_cmd = os.path.join(npm_global, "gws.cmd")
    if not os.path.exists(gws_cmd):
        gws_cmd = "gws"

    # Check gws installed
    try:
        r = subprocess.run([gws_cmd, "--version"], capture_output=True, text=True,
                           timeout=10, env=env)
        if r.returncode != 0:
            return {"gws_installed": False, "authenticated": False, "user": None}
        gws_version = r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"gws_installed": False, "authenticated": False, "user": None}

    # Check auth status
    try:
        r = subprocess.run([gws_cmd, "auth", "status", "--format", "json"],
                           capture_output=True, text=True, timeout=10, env=env)
        output = r.stdout.strip()
        if "authenticated" in output.lower() or "@" in output:
            # Try to extract user email
            import re
            emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', output)
            return {"gws_installed": True, "gws_version": gws_version,
                    "authenticated": True, "user": emails[0] if emails else "authenticated"}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return {"gws_installed": True, "gws_version": gws_version,
            "authenticated": False, "user": None}


def settings_page(page: ft.Page, llm: LLMClient):
    cfg = _load_config()

    # ── Google Account Section ──────────────────────────────────────────────

    env_data = _load_env()
    gws_status = _check_gws_auth()

    client_id_tf = toss_input(
        "Client ID", value=env_data.get("GOOGLE_WORKSPACE_CLI_CLIENT_ID", ""),
        width=480, hint_text="xxxx.apps.googleusercontent.com",
    )
    client_secret_tf = toss_input(
        "Client Secret", value=env_data.get("GOOGLE_WORKSPACE_CLI_CLIENT_SECRET", ""),
        password=True, can_reveal_password=True, width=480,
    )

    # Status indicator
    def _make_status_row(status):
        if not status["gws_installed"]:
            return ft.Row([
                ft.Container(width=10, height=10, border_radius=5, bgcolor=T.RED),
                ft.Text("gws 미설치", size=13, color=T.RED, weight=ft.FontWeight.W_500),
                ft.Text("npm install -g @googleworkspace/cli", size=11, color=T.TEXT_SUB),
            ], spacing=8)
        if status["authenticated"]:
            return ft.Row([
                ft.Container(width=10, height=10, border_radius=5, bgcolor=T.GREEN),
                ft.Text("연동 완료", size=13, color=T.GREEN, weight=ft.FontWeight.W_500),
                ft.Text(status.get("user", ""), size=12, color=T.TEXT_SUB),
            ], spacing=8)
        return ft.Row([
            ft.Container(width=10, height=10, border_radius=5, bgcolor=T.ORANGE),
            ft.Text("미연동", size=13, color=T.ORANGE, weight=ft.FontWeight.W_500),
            ft.Text("아래에서 로그인하세요", size=12, color=T.TEXT_SUB),
        ], spacing=8)

    google_status_row = ft.Container(content=_make_status_row(gws_status))
    google_action_status = ft.Text("", size=T.CAPTION_SIZE)

    def save_oauth_click(e):
        cid = client_id_tf.value.strip()
        csec = client_secret_tf.value.strip()
        if not cid or not csec:
            google_action_status.value = "Client ID와 Secret을 모두 입력하세요."
            google_action_status.color = T.RED
            page.update()
            return
        _save_env(cid, csec)
        google_action_status.value = "OAuth 키 저장 완료"
        google_action_status.color = T.GREEN
        page.update()

    def _show_snack(msg, color=T.RED):
        page.snack_bar = ft.SnackBar(ft.Text(msg, color="white", size=14), bgcolor=color, duration=5000)
        page.snack_bar.open = True
        page.update()

    def login_click(e):
        try:
            cid = client_id_tf.value.strip()
            csec = client_secret_tf.value.strip()
            if not cid or not csec:
                _show_snack("먼저 OAuth Client ID와 Secret을 입력하고 저장하세요!")
                google_action_status.value = "먼저 OAuth 키를 입력하고 저장하세요."
                google_action_status.color = T.RED
                page.update()
                return

            # Save env first
            _save_env(cid, csec)

            _show_snack("브라우저가 열립니다. 구글 계정으로 로그인하세요...", T.BLUE)
            google_action_status.value = "브라우저가 열립니다. 구글 계정으로 로그인하세요..."
            google_action_status.color = T.BLUE
            page.update()
        except Exception as ex:
            _show_snack(f"로그인 시작 오류: {ex}")
            return

        def do_login():
            import shutil
            env = os.environ.copy()
            npm_global = os.path.join(os.environ.get("APPDATA", ""), "npm")
            # 가능한 모든 경로 추가
            extra_paths = [
                npm_global,
                r"C:\Program Files\nodejs",
                r"C:\Program Files (x86)\nodejs",
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python312", "Scripts"),
            ]
            env["PATH"] = ";".join(extra_paths) + ";" + env.get("PATH", "")
            env["GOOGLE_WORKSPACE_CLI_CLIENT_ID"] = cid
            env["GOOGLE_WORKSPACE_CLI_CLIENT_SECRET"] = csec

            # gws 실행파일 찾기
            gws_cmd = None
            # 1) npm global 폴더
            for name in ["gws.cmd", "gws.ps1", "gws"]:
                p = os.path.join(npm_global, name)
                if os.path.exists(p):
                    gws_cmd = p
                    break
            # 2) PATH에서 찾기
            if not gws_cmd:
                gws_cmd = shutil.which("gws", path=env["PATH"])
            # 3) 최후 시도
            if not gws_cmd:
                gws_cmd = "gws"

            try:
                # gws auth login은 브라우저를 열어야 하므로 콘솔 창으로 실행
                process = subprocess.Popen(
                    [gws_cmd, "auth", "login"],
                    env=env,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
                process.wait(timeout=120)

                # Re-check status
                new_status = _check_gws_auth()
                if new_status["authenticated"]:
                    google_action_status.value = f"로그인 성공! ({new_status.get('user', '')})"
                    google_action_status.color = T.GREEN
                    google_status_row.content = _make_status_row(new_status)
                else:
                    google_action_status.value = "로그인이 완료되지 않았습니다. 다시 시도하세요."
                    google_action_status.color = T.RED
            except subprocess.TimeoutExpired:
                process.kill()
                _show_snack("타임아웃 (2분). 다시 시도하세요.", T.ORANGE)
                google_action_status.value = "타임아웃 (2분). 다시 시도하세요."
                google_action_status.color = T.ORANGE
            except FileNotFoundError:
                msg = f"gws CLI를 찾을 수 없습니다. install.bat를 다시 실행하세요. (경로: {gws_cmd})"
                _show_snack(msg)
                google_action_status.value = msg
                google_action_status.color = T.RED
            except Exception as ex:
                msg = f"오류: {str(ex)[:200]}"
                _show_snack(msg)
                google_action_status.value = msg
                google_action_status.color = T.RED
            page.update()

        threading.Thread(target=do_login, daemon=True).start()

    def refresh_status_click(e):
        new_status = _check_gws_auth()
        google_status_row.content = _make_status_row(new_status)
        google_action_status.value = "상태 새로고침 완료"
        google_action_status.color = T.BLUE
        page.update()

    def logout_click(e):
        google_action_status.value = "연동 해제 중..."
        google_action_status.color = T.BLUE
        page.update()

        def do_logout():
            env = os.environ.copy()
            npm_global = os.path.join(os.environ.get("APPDATA", ""), "npm")
            env["PATH"] = npm_global + ";" + r"C:\Program Files\nodejs;" + env.get("PATH", "")
            gws_cmd = os.path.join(npm_global, "gws.cmd")
            if not os.path.exists(gws_cmd):
                gws_cmd = "gws"

            try:
                subprocess.run(
                    [gws_cmd, "auth", "revoke"],
                    capture_output=True, text=True,
                    timeout=30, encoding="utf-8", env=env,
                )
                new_status = _check_gws_auth()
                if not new_status["authenticated"]:
                    google_action_status.value = "연동 해제 완료. 다른 계정으로 다시 로그인할 수 있습니다."
                    google_action_status.color = T.GREEN
                    google_status_row.content = _make_status_row(new_status)
                else:
                    google_action_status.value = "연동 해제 실패. 수동으로 해제하세요."
                    google_action_status.color = T.RED
            except Exception as ex:
                google_action_status.value = f"오류: {str(ex)[:100]}"
                google_action_status.color = T.RED
            page.update()

        threading.Thread(target=do_logout, daemon=True).start()

    def clear_keys_click(e):
        client_id_tf.value = ""
        client_secret_tf.value = ""
        env_path = _env_path()
        if os.path.exists(env_path):
            os.remove(env_path)
        os.environ.pop("GOOGLE_WORKSPACE_CLI_CLIENT_ID", None)
        os.environ.pop("GOOGLE_WORKSPACE_CLI_CLIENT_SECRET", None)
        google_action_status.value = "OAuth 키 삭제 완료"
        google_action_status.color = T.GREEN
        page.update()

    google_setup_steps = ft.Container(
        content=ft.Column([
            ft.Text("1. console.cloud.google.com 에서 프로젝트 생성", size=12, color=T.TEXT_SUB),
            ft.Text("2. Gmail, Calendar, Drive, Sheets API 활성화", size=12, color=T.TEXT_SUB),
            ft.Text("3. OAuth 동의 화면 설정 → 테스트 사용자에 본인 이메일 추가", size=12, color=T.TEXT_SUB),
            ft.Text("4. OAuth 클라이언트 ID (데스크톱 앱) 생성 → 아래에 붙여넣기", size=12, color=T.TEXT_SUB),
        ], spacing=4),
        bgcolor=T.GREY_50,
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
    )

    # ── LLM Section ─────────────────────────────────────────────────────────

    provider_dd = ft.Dropdown(
        label="LLM Provider",
        options=[
            ft.dropdown.Option("gemini", "Gemini (Google)"),
            ft.dropdown.Option("claude", "Claude (Anthropic)"),
            ft.dropdown.Option("openai", "OpenAI"),
        ],
        value=cfg.get("provider", "gemini"),
        width=320,
        border_radius=T.BTN_RADIUS,
        border_color=T.BORDER,
        focused_border_color=T.BLUE,
        label_style=ft.TextStyle(color=T.TEXT_SUB, size=13),
        text_style=ft.TextStyle(color=T.TEXT, size=14),
    )
    api_key_tf = toss_input(
        "API Key", value=cfg.get("api_key", ""),
        password=True, can_reveal_password=True, width=480,
    )
    model_tf = toss_input(
        "Model (optional)", value=cfg.get("model", ""),
        width=480, hint_text="gemini-2.5-flash / claude-sonnet-4-20250514 / gpt-4o-mini",
    )
    status_text = ft.Text("", size=T.CAPTION_SIZE)

    def save_click(e):
        provider = provider_dd.value
        api_key = api_key_tf.value.strip()
        model = model_tf.value.strip() or None

        if not api_key:
            status_text.value = "API Key를 입력하세요."
            status_text.color = T.RED
            page.update()
            return

        llm.configure(provider, api_key, model)
        _save_config({"provider": provider, "api_key": api_key, "model": model or ""})
        status_text.value = f"{provider} 설정이 저장되었습니다"
        status_text.color = T.GREEN
        page.update()

    api_cards = []
    providers = [
        ("Gemini", "aistudio.google.com/apikey", "무료 tier 사용 가능", T.BLUE),
        ("Claude", "console.anthropic.com", "$5 크레딧 충전 필요", T.ORANGE),
        ("OpenAI", "platform.openai.com", "$5 크레딧 충전 필요", T.GREEN),
    ]
    for name, url, note, color in providers:
        api_cards.append(
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(name[0], size=14, weight=ft.FontWeight.W_700, color=T.CARD),
                        width=36, height=36, border_radius=10, bgcolor=color,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(name, size=14, weight=ft.FontWeight.W_600, color=T.TEXT),
                        ft.Text(f"{url}  ·  {note}", size=11, color=T.TEXT_SUB),
                    ], spacing=1, expand=True),
                ], spacing=12),
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                border=ft.border.all(1, T.BORDER),
                border_radius=12,
            )
        )

    return ft.Column([
        ft.Text("설정", size=T.TITLE_SIZE, weight=ft.FontWeight.W_800, color=T.TEXT),
        ft.Container(height=8),

        # Google Account card
        toss_card(ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=20, color=T.BLUE),
                    width=36, height=36, border_radius=10, bgcolor=T.BLUE_LIGHT,
                    alignment=ft.Alignment(0, 0),
                ),
                section_title("Google 계정 연동", "Gmail, Calendar, Drive, Sheets 사용에 필요합니다"),
            ], spacing=12),
            ft.Container(height=8),
            google_status_row,
            ft.Container(height=12),
            google_setup_steps,
            ft.Container(height=12),
            client_id_tf,
            ft.Container(height=8),
            client_secret_tf,
            ft.Container(height=12),
            ft.Row([
                toss_btn("키 저장", save_oauth_click, ft.Icons.SAVE),
                ft.Container(width=8),
                toss_btn("구글 로그인", login_click, ft.Icons.LOGIN),
                ft.Container(width=8),
                toss_btn("상태 새로고침", refresh_status_click, ft.Icons.REFRESH, primary=False),
            ], spacing=0),
            ft.Container(height=8),
            ft.Row([
                toss_btn("연동 해제", logout_click, ft.Icons.LOGOUT, primary=False),
                ft.Container(width=8),
                toss_btn("키 삭제", clear_keys_click, ft.Icons.DELETE_OUTLINE, primary=False),
            ], spacing=0),
            ft.Container(height=4),
            google_action_status,
        ], spacing=0)),
        ft.Container(height=16),

        # LLM card
        toss_card(ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_AWESOME, size=20, color=T.BLUE),
                    width=36, height=36, border_radius=10, bgcolor=T.BLUE_LIGHT,
                    alignment=ft.Alignment(0, 0),
                ),
                section_title("LLM 설정", "AI 비서에서 사용할 모델을 선택합니다"),
            ], spacing=12),
            ft.Container(height=16),
            provider_dd,
            ft.Container(height=8),
            api_key_tf,
            ft.Container(height=8),
            model_tf,
            ft.Container(height=16),
            ft.Row([toss_btn("저장", save_click, ft.Icons.CHECK), ft.Container(width=8), status_text]),
        ], spacing=0)),
        ft.Container(height=16),

        # API guide card
        toss_card(ft.Column([
            section_title("API 키 발급 안내"),
            ft.Container(height=12),
            *api_cards,
        ], spacing=8)),
    ], scroll=ft.ScrollMode.AUTO, spacing=0)


# ── Chat Page ────────────────────────────────────────────────────────────────

def chat_page(page: ft.Page, llm: LLMClient):
    chat_list = ft.ListView(expand=True, spacing=12, auto_scroll=True, padding=ft.padding.symmetric(horizontal=4))
    input_tf = ft.TextField(
        hint_text="메시지를 입력하세요...",
        expand=True, on_submit=lambda e: send_click(e),
        multiline=False,
        border_radius=24,
        border_color=T.BORDER,
        focused_border_color=T.BLUE,
        content_padding=ft.padding.symmetric(horizontal=20, vertical=14),
        text_style=ft.TextStyle(color=T.TEXT, size=14),
        cursor_color=T.BLUE,
    )
    send_btn = ft.Container(
        content=ft.Icon(ft.Icons.ARROW_UPWARD_ROUNDED, size=20, color=T.CARD),
        width=40, height=40, border_radius=20, bgcolor=T.BLUE,
        alignment=ft.Alignment(0, 0),
        on_click=lambda e: send_click(e),
        ink=True,
    )
    loading = ft.ProgressRing(visible=False, width=20, height=20, color=T.BLUE, stroke_width=2)

    def add_bubble(text: str, is_user: bool):
        if is_user:
            bubble = ft.Container(
                content=ft.Text(text, size=14, color=T.CARD),
                bgcolor=T.BLUE,
                border_radius=ft.border_radius.only(
                    top_left=18, top_right=18, bottom_left=18, bottom_right=4,
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                margin=ft.margin.only(left=80),
            )
        else:
            bubble = ft.Container(
                content=ft.Markdown(text, selectable=True, auto_follow_links=True,
                                    extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED),
                bgcolor=T.GREY_100,
                border_radius=ft.border_radius.only(
                    top_left=18, top_right=18, bottom_left=4, bottom_right=18,
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                margin=ft.margin.only(right=80),
            )
        chat_list.controls.append(bubble)
        page.update()

    def send_click(e):
        msg = input_tf.value.strip()
        if not msg:
            return

        if not llm.is_configured():
            add_bubble("설정 탭에서 LLM API 키를 먼저 입력하세요.", False)
            return

        input_tf.value = ""
        loading.visible = True
        page.update()
        add_bubble(msg, True)

        def do_chat():
            response = llm.chat(msg)
            loading.visible = False
            add_bubble(response, False)

        threading.Thread(target=do_chat, daemon=True).start()

    def clear_click(e):
        chat_list.controls.clear()
        llm.history.clear()
        page.update()

    def quick_action(prompt):
        def handler(e):
            input_tf.value = prompt
            send_click(e)
        return handler

    quick_chips = []
    actions = [
        ("메일 요약", ft.Icons.MAIL_OUTLINE, "읽지 않은 메일 발신자별로 그룹핑해서 요약해줘"),
        ("오늘 일정", ft.Icons.TODAY, "오늘 일정 알려줘"),
        ("데드라인", ft.Icons.FLAG_OUTLINED, "이번 주 마감/납품 데드라인 확인해줘"),
        ("아침 루틴", ft.Icons.WB_SUNNY_OUTLINED, "오늘 메일 요약하고 일정도 같이 알려줘"),
    ]
    for label, icon, prompt in actions:
        quick_chips.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(icon, size=14, color=T.BLUE),
                    ft.Text(label, size=13, weight=ft.FontWeight.W_500, color=T.BLUE),
                ], spacing=6),
                border=ft.border.all(1, T.BLUE),
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                on_click=quick_action(prompt),
                ink=True,
            )
        )

    return ft.Column([
        ft.Row([
            ft.Text("AI 비서", size=T.TITLE_SIZE, weight=ft.FontWeight.W_800, color=T.TEXT),
            ft.Container(expand=True),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.REFRESH, size=14, color=T.TEXT_SUB),
                    ft.Text("초기화", size=12, color=T.TEXT_SUB),
                ], spacing=4),
                on_click=clear_click, ink=True,
                border_radius=8, padding=ft.padding.symmetric(horizontal=10, vertical=6),
            ),
        ]),
        ft.Row(quick_chips, spacing=8, scroll=ft.ScrollMode.AUTO),
        ft.Container(height=4),
        toss_card(chat_list, expand=True, padding=16),
        ft.Container(height=8),
        ft.Container(
            content=ft.Row([input_tf, loading, send_btn], spacing=8),
            bgcolor=T.CARD,
            border_radius=28,
            padding=ft.padding.only(left=4, right=4, top=4, bottom=4),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=12,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        ),
    ], expand=True, spacing=0)


# ── Mail Page ────────────────────────────────────────────────────────────────

def mail_page(page: ft.Page, llm: LLMClient):
    result_view = ft.ListView(expand=True, spacing=8, padding=ft.padding.symmetric(horizontal=4))
    status = ft.Text("", size=T.CAPTION_SIZE, color=T.TEXT_SUB)
    limit_tf = toss_input("개수", value="10", width=70)
    _current_mails = []

    def _mail_tile(icon, icon_color, title, subtitle, on_click=None):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, size=18, color=icon_color),
                    width=36, height=36, border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.1, icon_color),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(title, size=14, weight=ft.FontWeight.W_500, color=T.TEXT,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(subtitle, size=12, color=T.TEXT_SUB, max_lines=1),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, color=T.TEXT_CAPTION) if on_click else ft.Container(),
            ], spacing=12),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border_radius=12,
            bgcolor=T.CARD,
            on_click=on_click,
            ink=True,
        )

    def triage_click(e):
        status.value = "메일 조회 중..."
        result_view.controls.clear()
        page.update()

        def do_work():
            data = _run_qesg(f"qesg mail triage --limit {limit_tf.value}")
            status.value = ""
            if data.get("error") or data.get("code"):
                result_view.controls.append(
                    ft.Text(f"오류: {data.get('message', data.get('error', str(data)))}",
                            color=T.RED, size=13))
            else:
                messages = data.get("messages", [])
                _current_mails.clear()
                _current_mails.extend(messages)
                if not messages:
                    result_view.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=T.TEXT_CAPTION),
                                ft.Text("읽지 않은 메일이 없습니다", size=14, color=T.TEXT_SUB),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                            padding=40, alignment=ft.Alignment(0, 0),
                        ))

                grouped = {}
                for m in messages:
                    sender = m.get("from", "(알 수 없음)")
                    grouped.setdefault(sender, []).append(m)

                for sender, mails in grouped.items():
                    result_view.controls.append(ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(sender[0].upper(), size=13, weight=ft.FontWeight.W_700, color=T.CARD),
                                width=32, height=32, border_radius=16, bgcolor=T.BLUE,
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Text(f"{sender}", size=13, weight=ft.FontWeight.W_600,
                                    color=T.TEXT, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"{len(mails)}건", size=12, color=T.TEXT_SUB),
                            ft.Container(
                                content=ft.Icon(ft.Icons.HISTORY, size=14, color=T.BLUE),
                                width=32, height=32, border_radius=8,
                                bgcolor=T.BLUE_LIGHT, alignment=ft.Alignment(0, 0),
                                on_click=lambda e, s=sender: chat_history_click(s),
                                tooltip="대화이력",
                            ),
                            ft.Container(
                                content=ft.Icon(ft.Icons.EDIT_OUTLINED, size=14, color=T.BLUE),
                                width=32, height=32, border_radius=8,
                                bgcolor=T.BLUE_LIGHT, alignment=ft.Alignment(0, 0),
                                on_click=lambda e, s=sender, ms=mails: draft_reply_click(s, ms),
                                tooltip="회신 초안",
                            ),
                        ], spacing=8),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        bgcolor=T.GREY_50,
                        border_radius=12,
                    ))
                    for m in mails:
                        result_view.controls.append(
                            _mail_tile(
                                ft.Icons.MAIL_OUTLINE, T.BLUE,
                                m.get("subject", "(제목 없음)"),
                                m.get("date", ""),
                                on_click=lambda e, mid=m.get("id"): read_mail(mid),
                            ))
            page.update()

        threading.Thread(target=do_work, daemon=True).start()

    def chat_history_click(sender_name):
        name = sender_name.split("<")[0].strip().strip('"') if "<" in sender_name else sender_name.split("@")[0]
        status.value = f"{name} 대화이력 조회 중..."
        result_view.controls.clear()
        page.update()

        def do_work():
            data = _run_qesg(f'qesg mail chat --with "{name}"')
            status.value = ""
            threads = data.get("threads", [])
            if not threads:
                messages = data.get("messages", [])
                if messages:
                    threads = messages
                else:
                    result_view.controls.append(ft.Text(f"{name}과(와)의 대화이력이 없습니다.", size=13, color=T.TEXT_SUB))
                    page.update()
                    return

            result_view.controls.append(
                ft.Container(
                    content=ft.Text(f"{name} 대화이력", size=T.HEADING_SIZE, weight=ft.FontWeight.W_700, color=T.TEXT),
                    padding=ft.padding.only(bottom=8),
                ))
            if isinstance(threads, list):
                for t in threads:
                    if isinstance(t, dict):
                        result_view.controls.append(
                            _mail_tile(ft.Icons.CHAT_BUBBLE_OUTLINE, T.GREEN,
                                       t.get("subject", t.get("snippet", str(t))),
                                       t.get("date", "")))
                    else:
                        result_view.controls.append(ft.Text(str(t)[:200], size=12, color=T.TEXT_SUB))
            else:
                result_view.controls.append(ft.Text(str(threads)[:500], size=12, color=T.TEXT_SUB))
            page.update()

        threading.Thread(target=do_work, daemon=True).start()

    def draft_reply_click(sender_name, mails):
        if not llm.is_configured():
            status.value = "설정 탭에서 LLM API 키를 먼저 입력하세요."
            status.color = T.RED
            page.update()
            return

        name = sender_name.split("<")[0].strip().strip('"') if "<" in sender_name else sender_name.split("@")[0]
        subjects = ", ".join(m.get("subject", "") for m in mails[:3])

        draft_topic = toss_input("회신 주제/방향", hint_text="예: 일정 확인했고 3월 15일 가능하다고",
                                 width=500, multiline=True, min_lines=2)
        draft_result = ft.Text("", selectable=True, size=13, color=T.TEXT)
        draft_loading = ft.ProgressRing(visible=False, width=20, height=20, color=T.BLUE, stroke_width=2)

        def generate_draft(e):
            topic = draft_topic.value.strip()
            if not topic:
                draft_result.value = "회신 방향을 입력해주세요."
                page.update()
                return
            draft_loading.visible = True
            draft_result.value = "AI가 초안 작성 중..."
            draft_result.color = T.TEXT_SUB
            page.update()

            def do_draft():
                prompt = (
                    f"{name}에게 회신 초안을 작성해주세요.\n"
                    f"관련 메일 제목: {subjects}\n"
                    f"회신 방향: {topic}\n\n"
                    f"먼저 대화이력을 확인하고, 맥락에 맞는 자연스러운 비즈니스 메일 초안을 작성해주세요. "
                    f"메일 본문만 작성하세요 (인사말, 본론, 마무리 포함)."
                )
                response = llm.chat(prompt)
                draft_loading.visible = False
                draft_result.value = response
                draft_result.color = T.TEXT
                page.update()

            threading.Thread(target=do_draft, daemon=True).start()

        dlg = ft.AlertDialog(
            title=ft.Text(f"{name}에게 회신", weight=ft.FontWeight.W_700, size=16, color=T.TEXT),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"관련: {subjects}", size=12, color=T.TEXT_SUB),
                    ft.Container(height=8),
                    draft_topic,
                    ft.Container(height=8),
                    toss_btn("AI 초안 생성", generate_draft, ft.Icons.AUTO_AWESOME),
                    draft_loading,
                    ft.Container(height=8),
                    draft_result,
                ], scroll=ft.ScrollMode.AUTO),
                width=560, height=420,
            ),
            actions=[ft.TextButton("닫기", on_click=lambda e: (setattr(dlg, 'open', False), page.update()))],
            shape=ft.RoundedRectangleBorder(radius=T.CARD_RADIUS),
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def read_mail(mail_id):
        status.value = "메일 읽는 중..."
        page.update()

        def do_work():
            data = _run_qesg(f'qesg mail read {mail_id}')
            status.value = ""

            body_text = data.get("body", data.get("raw", str(data)))
            subject = data.get("subject", "메일")
            sender = data.get("from", "")

            import re
            date_patterns = re.findall(
                r'(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}월\s*\d{1,2}일)',
                body_text
            )
            schedule_hint = ""
            if date_patterns:
                schedule_hint = f"일정 감지: {', '.join(date_patterns[:3])}"

            dlg = ft.AlertDialog(
                title=ft.Text(subject, weight=ft.FontWeight.W_700, size=16, color=T.TEXT),
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Text(f"From: {sender}", size=12, color=T.TEXT_SUB),
                            padding=ft.padding.only(bottom=8),
                        ),
                        ft.Container(height=1, bgcolor=T.BORDER),
                        ft.Container(height=8),
                        ft.Text(body_text, selectable=True, size=13, color=T.TEXT),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.EVENT, size=14, color=T.BLUE),
                                ft.Text(schedule_hint, color=T.BLUE, size=12, weight=ft.FontWeight.W_600),
                            ], spacing=6),
                            bgcolor=T.BLUE_LIGHT, border_radius=8,
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            visible=bool(schedule_hint),
                        ),
                    ], scroll=ft.ScrollMode.AUTO),
                    width=560, height=380,
                ),
                actions=[ft.TextButton("닫기", on_click=lambda e: (setattr(dlg, 'open', False), page.update()))],
                shape=ft.RoundedRectangleBorder(radius=T.CARD_RADIUS),
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        threading.Thread(target=do_work, daemon=True).start()

    query_tf = toss_input("검색어", hint_text="from:홍길동", width=280)

    def search_click(e):
        if not query_tf.value.strip():
            return
        status.value = "검색 중..."
        result_view.controls.clear()
        page.update()

        def do_work():
            data = _run_qesg(f'qesg mail list --query "{query_tf.value}"')
            status.value = ""
            messages = data.get("messages", [])
            if not messages:
                result_view.controls.append(ft.Text("검색 결과가 없습니다.", size=13, color=T.TEXT_SUB))
            for m in messages:
                result_view.controls.append(
                    _mail_tile(ft.Icons.MAIL_OUTLINE, T.TEXT_SUB,
                               m.get("subject", "(제목 없음)"),
                               f"{m.get('from', '')} · {m.get('date', '')}"))
            page.update()

        threading.Thread(target=do_work, daemon=True).start()

    chat_name_tf = toss_input("이름", hint_text="홍길동", width=160)
    chat_topic_tf = toss_input("주제 (선택)", hint_text="프로젝트", width=160)

    def chat_click(e):
        if not chat_name_tf.value.strip():
            return
        chat_history_click(chat_name_tf.value)

    return ft.Column([
        ft.Text("메일", size=T.TITLE_SIZE, weight=ft.FontWeight.W_800, color=T.TEXT),
        ft.Container(height=8),
        toss_card(ft.Column([
            ft.Row([
                toss_btn("읽지 않은 메일", triage_click, ft.Icons.INBOX_OUTLINED),
                limit_tf,
                ft.Container(expand=True),
                query_tf,
                toss_btn("검색", search_click, ft.Icons.SEARCH, primary=False),
            ], spacing=8),
            ft.Container(height=8),
            ft.Row([
                ft.Text("대화이력", size=13, color=T.TEXT_SUB),
                chat_name_tf, chat_topic_tf,
                toss_btn("조회", chat_click, ft.Icons.HISTORY, primary=False),
            ], spacing=8),
        ], spacing=0), padding=16),
        ft.Container(height=4),
        status,
        result_view,
    ], expand=True, spacing=0)


# ── Calendar Page ────────────────────────────────────────────────────────────

def calendar_page(page: ft.Page):
    result_view = ft.ListView(expand=True, spacing=8, padding=ft.padding.symmetric(horizontal=4))
    status = ft.Text("", size=T.CAPTION_SIZE, color=T.TEXT_SUB)

    def agenda_click(e):
        status.value = "일정 조회 중..."
        result_view.controls.clear()
        page.update()

        def do_work():
            data = _run_qesg("qesg schedule agenda")
            status.value = ""
            events = data.get("events", [])
            if not events:
                result_view.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.EVENT_AVAILABLE, size=48, color=T.TEXT_CAPTION),
                            ft.Text("예정된 일정이 없습니다", size=14, color=T.TEXT_SUB),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                        padding=40, alignment=ft.Alignment(0, 0),
                    ))
            elif isinstance(events, list):
                for ev in events:
                    if isinstance(ev, dict):
                        result_view.controls.append(ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Icon(ft.Icons.CIRCLE, size=8, color=T.BLUE),
                                    width=32, height=32, alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column([
                                    ft.Text(ev.get("summary", "(제목 없음)"),
                                            size=14, weight=ft.FontWeight.W_500, color=T.TEXT),
                                    ft.Text(f"{ev.get('start', '')} ~ {ev.get('end', '')}",
                                            size=12, color=T.TEXT_SUB),
                                ], spacing=2, expand=True),
                            ], spacing=8),
                            padding=ft.padding.symmetric(horizontal=16, vertical=12),
                            bgcolor=T.CARD, border_radius=12,
                        ))
                    else:
                        result_view.controls.append(ft.Text(str(ev), size=12, color=T.TEXT_SUB))
            else:
                result_view.controls.append(ft.Text(str(events), size=12, color=T.TEXT_SUB))
            page.update()

        threading.Thread(target=do_work, daemon=True).start()

    title_tf = toss_input("제목", width=200)
    date_tf = toss_input("날짜", hint_text="YYYY-MM-DD", width=150)
    time_tf = toss_input("시간", hint_text="HH:MM", width=120)
    add_status = ft.Text("", size=T.CAPTION_SIZE)

    def add_click(e):
        if not title_tf.value or not date_tf.value:
            add_status.value = "제목과 날짜를 입력하세요."
            add_status.color = T.RED
            page.update()
            return
        cmd = f'qesg schedule add --title "{title_tf.value}" --date {date_tf.value}'
        if time_tf.value:
            cmd += f" --time {time_tf.value}"
        cmd += " --dry-run"
        add_status.value = "추가 중..."
        add_status.color = T.TEXT_SUB
        page.update()

        def do_work():
            data = _run_qesg(cmd)
            if data.get("status") == "dry_run":
                add_status.value = f"[미리보기] {title_tf.value} — {date_tf.value}"
                add_status.color = T.ORANGE
            else:
                add_status.value = f"완료: {data.get('message', str(data))}"
                add_status.color = T.GREEN
            page.update()

        threading.Thread(target=do_work, daemon=True).start()

    days_tf = toss_input("일수", value="14", width=70)

    def deadline_click(e):
        status.value = "데드라인 조회 중..."
        result_view.controls.clear()
        page.update()

        def do_work():
            data = _run_qesg(f"qesg schedule deadlines --days {days_tf.value}")
            status.value = ""
            deadlines = data.get("deadlines", [])
            if not deadlines:
                result_view.controls.append(ft.Text("다가오는 데드라인이 없습니다.", size=13, color=T.TEXT_SUB))
            elif isinstance(deadlines, list):
                for dl in deadlines:
                    if isinstance(dl, dict):
                        result_view.controls.append(ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Icon(ft.Icons.FLAG, size=16, color=T.ORANGE),
                                    width=32, height=32, border_radius=8,
                                    bgcolor=ft.Colors.with_opacity(0.1, T.ORANGE),
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column([
                                    ft.Text(dl.get("summary", ""), size=14, weight=ft.FontWeight.W_500, color=T.TEXT),
                                    ft.Text(str(dl.get("start", "")), size=12, color=T.TEXT_SUB),
                                ], spacing=2, expand=True),
                            ], spacing=12),
                            padding=ft.padding.symmetric(horizontal=16, vertical=12),
                            bgcolor=T.CARD, border_radius=12,
                        ))
            page.update()

        threading.Thread(target=do_work, daemon=True).start()

    return ft.Column([
        ft.Text("캘린더", size=T.TITLE_SIZE, weight=ft.FontWeight.W_800, color=T.TEXT),
        ft.Container(height=8),
        toss_card(ft.Column([
            ft.Row([
                toss_btn("오늘 일정", agenda_click, ft.Icons.TODAY),
                ft.Container(width=8),
                toss_btn("데드라인", deadline_click, ft.Icons.FLAG_OUTLINED, primary=False),
                days_tf,
            ], spacing=8),
        ]), padding=16),
        ft.Container(height=4),
        status,
        result_view,
        ft.Container(height=12),
        toss_card(ft.Column([
            section_title("일정 추가"),
            ft.Container(height=12),
            ft.Row([title_tf, date_tf, time_tf,
                    toss_btn("추가 (미리보기)", add_click, ft.Icons.ADD)], spacing=8),
            add_status,
        ]), padding=16),
    ], expand=True, spacing=0)


# ── Drive Page ───────────────────────────────────────────────────────────────

def drive_page(page: ft.Page):
    result_view = ft.ListView(expand=True, spacing=8, padding=ft.padding.symmetric(horizontal=4))
    status = ft.Text("", size=T.CAPTION_SIZE, color=T.TEXT_SUB)
    query_tf = toss_input("검색어", width=300)

    def _file_icon(mime):
        if "spreadsheet" in mime:
            return ft.Icons.TABLE_CHART, T.GREEN
        elif "presentation" in mime:
            return ft.Icons.SLIDESHOW, T.ORANGE
        elif "folder" in mime:
            return ft.Icons.FOLDER, T.BLUE
        return ft.Icons.DESCRIPTION, T.TEXT_SUB

    def search_click(e):
        if not query_tf.value.strip():
            return
        status.value = "검색 중..."
        result_view.controls.clear()
        page.update()

        def do_work():
            data = _run_qesg(f'qesg doc search "{query_tf.value}"')
            status.value = ""
            files = data.get("files", [])
            if not files:
                result_view.controls.append(ft.Text("검색 결과가 없습니다.", size=13, color=T.TEXT_SUB))
            elif isinstance(files, list):
                for f_item in files:
                    if isinstance(f_item, dict):
                        icon, color = _file_icon(f_item.get("mimeType", ""))
                        result_view.controls.append(ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Icon(icon, size=18, color=color),
                                    width=36, height=36, border_radius=10,
                                    bgcolor=ft.Colors.with_opacity(0.1, color),
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column([
                                    ft.Text(f_item.get("name", ""), size=14,
                                            weight=ft.FontWeight.W_500, color=T.TEXT, max_lines=1),
                                    ft.Text(f_item.get("mimeType", "")[:40], size=11, color=T.TEXT_SUB),
                                ], spacing=2, expand=True),
                            ], spacing=12),
                            padding=ft.padding.symmetric(horizontal=16, vertical=12),
                            bgcolor=T.CARD, border_radius=12,
                        ))
            page.update()

        threading.Thread(target=do_work, daemon=True).start()

    type_dd = ft.Dropdown(
        label="유형", width=140,
        options=[
            ft.dropdown.Option("any", "전체"),
            ft.dropdown.Option("doc", "문서"),
            ft.dropdown.Option("sheet", "스프레드시트"),
            ft.dropdown.Option("slide", "프레젠테이션"),
            ft.dropdown.Option("pdf", "PDF"),
        ],
        value="any",
        border_radius=T.BTN_RADIUS,
        border_color=T.BORDER,
        focused_border_color=T.BLUE,
        label_style=ft.TextStyle(color=T.TEXT_SUB, size=13),
        text_style=ft.TextStyle(color=T.TEXT, size=14),
    )

    def list_click(e):
        status.value = "파일 목록 조회 중..."
        result_view.controls.clear()
        page.update()

        def do_work():
            cmd = f"qesg doc list --type {type_dd.value}"
            if query_tf.value.strip():
                cmd += f' --query "{query_tf.value}"'
            data = _run_qesg(cmd)
            status.value = ""
            files = data.get("files", [])
            if not files:
                result_view.controls.append(ft.Text("파일이 없습니다.", size=13, color=T.TEXT_SUB))
            elif isinstance(files, list):
                for f_item in files:
                    if isinstance(f_item, dict):
                        result_view.controls.append(ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.DESCRIPTION, size=16, color=T.TEXT_SUB),
                                ft.Text(f_item.get("name", ""), size=14, color=T.TEXT, expand=True, max_lines=1),
                            ], spacing=12),
                            padding=ft.padding.symmetric(horizontal=16, vertical=10),
                            bgcolor=T.CARD, border_radius=10,
                        ))
            page.update()

        threading.Thread(target=do_work, daemon=True).start()

    return ft.Column([
        ft.Text("Drive", size=T.TITLE_SIZE, weight=ft.FontWeight.W_800, color=T.TEXT),
        ft.Container(height=8),
        toss_card(ft.Column([
            ft.Row([
                query_tf,
                toss_btn("검색", search_click, ft.Icons.SEARCH),
                ft.Container(width=12),
                type_dd,
                toss_btn("목록", list_click, ft.Icons.LIST, primary=False),
            ], spacing=8),
        ]), padding=16),
        ft.Container(height=4),
        status,
        result_view,
    ], expand=True, spacing=0)


# ── Sheets Page ──────────────────────────────────────────────────────────────

def sheets_page(page: ft.Page):
    result_view = ft.ListView(expand=True, spacing=4, padding=ft.padding.symmetric(horizontal=4))
    status = ft.Text("", size=T.CAPTION_SIZE, color=T.TEXT_SUB)

    sid_tf = toss_input("스프레드시트 ID", width=340)
    range_tf = toss_input("범위", value="Sheet1", width=180)

    def read_click(e):
        if not sid_tf.value.strip():
            return
        status.value = "시트 읽는 중..."
        result_view.controls.clear()
        page.update()

        def do_work():
            data = _run_qesg(f'qesg data read {sid_tf.value} --range "{range_tf.value}"')
            status.value = ""
            sheet_data = data.get("data")
            if sheet_data:
                if isinstance(sheet_data, dict):
                    values = sheet_data.get("values", [])
                elif isinstance(sheet_data, list):
                    values = sheet_data
                else:
                    values = []

                if values:
                    for i, row in enumerate(values[:50]):
                        if isinstance(row, list):
                            bg = T.GREY_50 if i % 2 == 0 else T.CARD
                            result_view.controls.append(ft.Container(
                                content=ft.Text(" | ".join(str(c) for c in row), size=12, color=T.TEXT),
                                bgcolor=bg, padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                border_radius=6,
                            ))
                        else:
                            result_view.controls.append(ft.Text(str(row), size=12, color=T.TEXT))
                else:
                    result_view.controls.append(ft.Text("데이터가 없습니다.", size=13, color=T.TEXT_SUB))
            else:
                result_view.controls.append(ft.Text(str(data), size=12, color=T.TEXT_SUB))
            page.update()

        threading.Thread(target=do_work, daemon=True).start()

    search_tf = toss_input("스프레드시트 검색", width=300)

    def search_click(e):
        if not search_tf.value.strip():
            return
        status.value = "검색 중..."
        result_view.controls.clear()
        page.update()

        def do_work():
            data = _run_qesg(f'qesg data search --query "{search_tf.value}"')
            status.value = ""
            sheets = data.get("spreadsheets", [])
            if not sheets:
                result_view.controls.append(ft.Text("검색 결과가 없습니다.", size=13, color=T.TEXT_SUB))
            elif isinstance(sheets, list):
                for s in sheets:
                    if isinstance(s, dict):
                        result_view.controls.append(ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Icon(ft.Icons.TABLE_CHART, size=18, color=T.GREEN),
                                    width=36, height=36, border_radius=10,
                                    bgcolor=ft.Colors.with_opacity(0.1, T.GREEN),
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column([
                                    ft.Text(s.get("name", ""), size=14, weight=ft.FontWeight.W_500, color=T.TEXT),
                                    ft.Text(s.get("id", ""), size=11, color=T.TEXT_CAPTION, max_lines=1),
                                ], spacing=2, expand=True),
                            ], spacing=12),
                            padding=ft.padding.symmetric(horizontal=16, vertical=12),
                            bgcolor=T.CARD, border_radius=12,
                            on_click=lambda e, sid=s.get("id"): (
                                setattr(sid_tf, 'value', sid), page.update()
                            ),
                            ink=True,
                        ))
            page.update()

        threading.Thread(target=do_work, daemon=True).start()

    return ft.Column([
        ft.Text("Sheets", size=T.TITLE_SIZE, weight=ft.FontWeight.W_800, color=T.TEXT),
        ft.Container(height=8),
        toss_card(ft.Column([
            section_title("스프레드시트 검색"),
            ft.Container(height=12),
            ft.Row([search_tf, toss_btn("검색", search_click, ft.Icons.SEARCH, primary=False)], spacing=8),
        ]), padding=16),
        ft.Container(height=12),
        toss_card(ft.Column([
            section_title("데이터 읽기"),
            ft.Container(height=12),
            ft.Row([sid_tf, range_tf, toss_btn("읽기", read_click, ft.Icons.TABLE_VIEW)], spacing=8),
        ]), padding=16),
        ft.Container(height=4),
        status,
        result_view,
    ], expand=True, spacing=0)


# ── Main App ─────────────────────────────────────────────────────────────────

def main(page: ft.Page):
    page.title = "QESG"
    page.window.width = 1060
    page.window.height = 720
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = T.BG
    page.padding = 0
    page.fonts = {
        "Pretendard": "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css",
    }
    page.theme = ft.Theme(
        color_scheme_seed=T.BLUE,
        font_family="Pretendard",
    )

    # ── Auto-update on launch ──
    def _run_update():
        result = _auto_update()
        if result == "updated":
            page.snack_bar = ft.SnackBar(
                ft.Text("최신 버전으로 업데이트됨! 앱을 재시작하면 적용됩니다.", color="white", size=14),
                bgcolor=T.GREEN, duration=5000,
            )
            page.snack_bar.open = True
            page.update()
        elif result == "error":
            page.snack_bar = ft.SnackBar(
                ft.Text("자동 업데이트 실패 (인터넷 연결 확인)", color="white", size=13),
                bgcolor=T.ORANGE, duration=3000,
            )
            page.snack_bar.open = True
            page.update()
        # "latest" or "skip" → 조용히 넘어감

    threading.Thread(target=_run_update, daemon=True).start()

    llm = LLMClient()

    cfg = _load_config()
    if cfg.get("provider") and cfg.get("api_key"):
        llm.configure(cfg["provider"], cfg["api_key"], cfg.get("model") or None)

    pages = {
        "chat": chat_page(page, llm),
        "mail": mail_page(page, llm),
        "calendar": calendar_page(page),
        "drive": drive_page(page),
        "sheets": sheets_page(page),
        "settings": settings_page(page, llm),
    }

    content = ft.Container(expand=True, padding=T.PAGE_PADDING, bgcolor=T.BG)
    content.content = pages["chat"]

    # Navigation state
    nav_items = [
        ("chat", ft.Icons.CHAT_BUBBLE_OUTLINE, ft.Icons.CHAT_BUBBLE, "AI 비서"),
        ("mail", ft.Icons.MAIL_OUTLINE, ft.Icons.MAIL, "메일"),
        ("calendar", ft.Icons.CALENDAR_TODAY_OUTLINED, ft.Icons.CALENDAR_TODAY, "캘린더"),
        ("drive", ft.Icons.FOLDER_OUTLINED, ft.Icons.FOLDER, "Drive"),
        ("sheets", ft.Icons.TABLE_CHART_OUTLINED, ft.Icons.TABLE_CHART, "Sheets"),
        ("settings", ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS, "설정"),
    ]

    nav_buttons = []
    selected_idx = {"value": 0}

    def nav_click(idx):
        def handler(e):
            selected_idx["value"] = idx
            key = nav_items[idx][0]
            content.content = pages[key]
            _update_nav()
            page.update()
        return handler

    def _update_nav():
        for i, btn_container in enumerate(nav_buttons):
            is_selected = i == selected_idx["value"]
            icon_control = btn_container.content.controls[0]
            label_control = btn_container.content.controls[1]
            icon_control.name = nav_items[i][2] if is_selected else nav_items[i][1]
            icon_control.color = T.BLUE if is_selected else T.TEXT_CAPTION
            label_control.color = T.BLUE if is_selected else T.TEXT_CAPTION
            label_control.weight = ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_400
            btn_container.bgcolor = T.BLUE_LIGHT if is_selected else "transparent"

    for i, (key, icon_off, icon_on, label) in enumerate(nav_items):
        is_selected = i == 0
        btn = ft.Container(
            content=ft.Column([
                ft.Icon(icon_on if is_selected else icon_off, size=22,
                        color=T.BLUE if is_selected else T.TEXT_CAPTION),
                ft.Text(label, size=11,
                        color=T.BLUE if is_selected else T.TEXT_CAPTION,
                        weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_400,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
               alignment=ft.MainAxisAlignment.CENTER),
            width=72, height=64,
            border_radius=14,
            bgcolor=T.BLUE_LIGHT if is_selected else "transparent",
            alignment=ft.Alignment(0, 0),
            on_click=nav_click(i),
            ink=True,
        )
        nav_buttons.append(btn)

    sidebar = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text("QESG", size=20, weight=ft.FontWeight.W_800, color=T.BLUE),
                    padding=ft.padding.only(top=20, bottom=16),
                    alignment=ft.Alignment(0, 0),
                ),
                *nav_buttons,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        width=88,
        bgcolor=T.CARD,
        padding=ft.padding.only(top=0, bottom=20, left=8, right=8),
        border=ft.border.only(right=ft.BorderSide(1, T.BORDER)),
    )

    page.add(
        ft.Row([sidebar, content], expand=True, spacing=0)
    )


def run():
    ft.app(main)


if __name__ == "__main__":
    run()
