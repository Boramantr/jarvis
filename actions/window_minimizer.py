import pygetwindow


def window_minimizer_action(parameters=None, player=None):
    try:
        active_window = pygetwindow.getActiveWindow()
        if active_window:
            active_window.minimize()
            return "Active window minimized successfully."
        else:
            return "No active window found."
    except Exception as e:
        return f"Error minimizing window: {e}"
