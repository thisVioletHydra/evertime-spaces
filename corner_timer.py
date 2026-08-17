#!/usr/bin/env python3
"""Часы в правом верхнем углу, когда системных часов не видно (как Corner Time)."""

from __future__ import annotations

import os
import signal
import sys

from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSColor,
    NSFont,
    NSMakeRect,
    NSPanel,
    NSScreen,
    NSShadow,
    NSSize,
    NSTextField,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
    NSWorkspace,
)
from Foundation import NSFileHandle, NSObject, NSTimer
from PyObjCTools import AppHelper
from Quartz import (
    CGWindowLevelForKey,
    CGWindowListCopyWindowInfo,
    kCGNullWindowID,
    kCGPopUpMenuWindowLevelKey,
    kCGWindowListOptionOnScreenOnly,
)

OVERLAY_LEVEL = CGWindowLevelForKey(kCGPopUpMenuWindowLevelKey)

MARGIN_RIGHT = 14.0
# ниже полосы менюбара (33pt): окна целиком внутри неё macOS на фуллскрин-спейсах не рисует
MARGIN_TOP = 36.0
FONT_SIZE = 13.0
TIME_FMT = "%H:%M"
TICK_S = 0.35

# виджеты менюбара (часы, Wi-Fi, батарея...): небольшие окна layer=25 у верха.
# Окно "Menubar" в списке висит всегда, даже на фуллскрине, а виджеты — только
# когда менюбар реально виден. Это и есть честный сигнал "системные часы на экране".
STATUS_LAYER = 25
STATUS_MAX_HEIGHT = 40.0
STATUS_MAX_WIDTH = 400.0


def format_time() -> str:
    from time import strftime

    return strftime(TIME_FMT)


def system_clock_visible() -> bool:
    infos = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    for info in infos or []:
        if int(info.get("kCGWindowLayer", -1)) != STATUS_LAYER:
            continue
        if float(info.get("kCGWindowAlpha", 1.0)) < 0.05:
            continue

        bounds = info.get("kCGWindowBounds") or {}
        is_menu_widget = (
            float(bounds.get("Y", 9999.0)) <= 1.0
            and float(bounds.get("Height", 9999.0)) <= STATUS_MAX_HEIGHT
            and float(bounds.get("Width", 9999.0)) <= STATUS_MAX_WIDTH
        )
        if is_menu_widget:
            return True

    return False


class ClockController(NSObject):
    window = None
    label = None

    def applicationDidFinishLaunching_(self, _notification) -> None:
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 80, 22))
        label.setStringValue_(format_time())
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        label.setFont_(NSFont.monospacedDigitSystemFontOfSize_weight_(FONT_SIZE, 0.0))
        # ~40% темнее чистого белого
        label.setTextColor_(NSColor.colorWithCalibratedWhite_alpha_(0.60, 1.0))

        shadow = NSShadow.alloc().init()
        shadow.setShadowColor_(NSColor.blackColor().colorWithAlphaComponent_(0.85))
        shadow.setShadowOffset_(NSSize(width=0, height=-1))
        shadow.setShadowBlurRadius_(3.0)
        label.setShadow_(shadow)
        label.sizeToFit()

        w = label.frame().size.width + 16
        h = label.frame().size.height + 4
        frame = NSScreen.mainScreen().frame()
        x = frame.origin.x + frame.size.width - w - MARGIN_RIGHT
        y = frame.origin.y + frame.size.height - h - MARGIN_TOP

        window = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, w, h),
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
            NSBackingStoreBuffered,
            False,
        )
        window.setLevel_(OVERLAY_LEVEL)
        window.setFloatingPanel_(True)
        window.setBecomesKeyOnlyIfNeeded_(True)
        window.setWorksWhenModal_(True)
        window.setOpaque_(False)
        window.setBackgroundColor_(NSColor.clearColor())
        window.setHasShadow_(False)
        window.setIgnoresMouseEvents_(True)
        window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )
        window.setHidesOnDeactivate_(False)
        window.setCanHide_(False)
        window.setContentView_(label)

        self.window = window
        self.label = label

        NSWorkspace.sharedWorkspace().notificationCenter().addObserver_selector_name_object_(
            self,
            "spaceChanged:",
            "NSWorkspaceActiveSpaceDidChangeNotification",
            None,
        )

        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            TICK_S,
            self,
            "tick:",
            None,
            True,
        )
        self.refreshClock()

    def spaceChanged_(self, _note) -> None:
        # список окон обновляется с лагом после свайпа — добиваем отложенно
        self.refreshClock()
        for delay in (0.2, 0.6):
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                delay,
                self,
                "delayedRefresh:",
                None,
                False,
            )

    def delayedRefresh_(self, _timer) -> None:
        self.refreshClock()

    def refreshClock(self) -> None:
        if self.label is None or self.window is None:
            return

        sys_clock = system_clock_visible()
        if os.environ.get("CORNER_DEBUG"):
            from time import strftime

            with open("/tmp/clock_dbg.log", "a") as f:
                fr = self.window.frame()
                f.write(
                    f"{strftime('%H:%M:%S')} sys_clock={sys_clock} "
                    f"visible={bool(self.window.isVisible())} "
                    f"frame=({fr.origin.x:.0f},{fr.origin.y:.0f},"
                    f"{fr.size.width:.0f},{fr.size.height:.0f}) "
                    f"level={self.window.level()}\n"
                )

        if sys_clock:
            self.window.orderOut_(None)
            return

        self.label.setStringValue_(format_time())
        self.label.sizeToFit()

        frame = NSScreen.mainScreen().frame()
        w = self.label.frame().size.width + 16
        h = self.label.frame().size.height + 4
        snap_x = frame.origin.x + frame.size.width - w - MARGIN_RIGHT
        snap_y = frame.origin.y + frame.size.height - h - MARGIN_TOP
        self.window.setFrame_display_(NSMakeRect(snap_x, snap_y, w, h), True)

        # macOS иногда сбрасывает level после смены Space — долбим заново
        self.window.setLevel_(OVERLAY_LEVEL)
        self.window.orderFrontRegardless()

    def tick_(self, _timer) -> None:
        # запасной выход: если байт уже в pipe, а readability handler не стрельнул
        if _wakeup_r is not None:
            try:
                if os.read(_wakeup_r, 64):
                    os._exit(130)
            except BlockingIOError:
                pass
            except InterruptedError:
                os._exit(130)
        self.refreshClock()


_delegate = None
_wakeup_r = None
_wakeup_w = None
_wakeup_handle = None


def _install_ctrl_c_kill() -> None:
    """CFRunLoop глотает SIGINT — будим его через pipe + NSFileHandle."""
    global _wakeup_r, _wakeup_w, _wakeup_handle

    _wakeup_r, _wakeup_w = os.pipe()
    os.set_blocking(_wakeup_r, False)
    os.set_blocking(_wakeup_w, False)

    # Python пишет байт в fd при любом сигнале
    signal.set_wakeup_fd(_wakeup_w)

    def on_signal(signum, _frame) -> None:
        os._exit(128 + int(signum))

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    handle = NSFileHandle.alloc().initWithFileDescriptor_closeOnDealloc_(
        _wakeup_r,
        False,
    )

    def on_readable(_fh) -> None:
        os._exit(130)

    handle.setReadabilityHandler_(on_readable)
    _wakeup_handle = handle


def main() -> None:
    global _delegate

    _install_ctrl_c_kill()

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    _delegate = ClockController.alloc().init()
    app.setDelegate_(_delegate)
    AppHelper.runEventLoop()
    sys.exit(0)


if __name__ == "__main__":
    main()
