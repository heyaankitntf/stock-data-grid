"""Stock Screener application package.

Modular structure:
  app.config       — constants, paths, environment
  app.styles       — theme palettes, CSS injection, FOUC bootstrap
  app.auth         — login, logout, session/cookie management
  app.portfolio    — holdings, trades, JSON persistence
  app.scanner      — yfinance scan + dataframe styling
  app.trading      — order preview, trade execution
  app.components   — reusable UI fragments (sidebar, hero, tabs)
"""
__all__ = []
