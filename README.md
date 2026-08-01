# 📈 CAR + DMA Super Breakout Scanner

A powerful stock screening application built with Streamlit that identifies NSE stocks breaking out above key moving averages with monotonically rising Cumulative Average Return (CAR). Includes virtual trading with live P&L tracking.

## ✨ Features

### 📊 Scanner
- **Technical Analysis**: Scans for stocks above 30, 50, and 200-day moving averages
- **CAR Filter**: Identifies stocks with monotonically rising CAR over 10 days
- **Parallel Processing**: Fast scanning with 10 concurrent workers
- **Real-time Progress**: Live progress tracking during scans
- **Export Results**: Download scan results as Excel files

### 💼 Mock Trading
- **Virtual Capital**: Start with ₹10,00,000 virtual money
- **Live Prices**: Fetch real-time stock prices via Yahoo Finance
- **Portfolio Tracking**: Monitor holdings, P&L, and portfolio value
- **Trade History**: Complete log of all buy/sell transactions
- **Risk-Free Practice**: Test strategies without real money

### 🎨 UI/UX
- **Dark/Light Themes**: Toggle between themes
- **Responsive Design**: Works on desktop and mobile
- **No FOUC**: Optimized CSS prevents layout shifts
- **Session Persistence**: "Remember me" functionality

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Stock-Data-Grid.git
cd Stock-Data-Grid/stock-screener
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

5. Open your browser:
```
http://localhost:8501
```

### Default Login
- **Username:** `admin`
- **Password:** `admin123`

⚠️ **Important:** Change these credentials in production!

## 📁 Project Structure

```
Stock-Data-Grid/
├── stock-screener/
│   ├── app.py              # Main Streamlit application
│   ├── requirements.txt    # Python dependencies
│   ├── settings.json       # Stock universe (gitignored)
│   ├── portfolio.json      # Trade data (gitignored)
│   ├── session.json        # Session data (gitignored)
│   └── .streamlit/
│       └── config.toml     # Streamlit configuration
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Stock Universe
Add/edit stocks in the sidebar under "Stock Universe". Stocks are automatically saved to `settings.json`.

### Streamlit Config
Edit `.streamlit/config.toml` for:
- Server settings
- Theme customization
- Performance tuning

## 📊 Screening Criteria

The scanner identifies stocks meeting **ALL** of these conditions:

1. **CMP > 30 DMA** - Current price above 30-day moving average
2. **CMP > 50 DMA** - Current price above 50-day moving average
3. **CMP > 200 DMA** - Current price above 200-day moving average
4. **CAR Rising** - Cumulative Average Return monotonically increasing over 10 days

## 🔒 Security Notes

- Session data stored in local files (not cookies)
- No external database required
- All data stays on your machine
- **Never commit** `session.json`, `portfolio.json`, or `settings.json`

## 🐛 Known Issues

- Yahoo Finance API may occasionally timeout (retry mechanism included)
- Scanning 200+ stocks takes 1-2 minutes (parallel processing optimized)

## 📝 License

This project is for **educational purposes only**. Not financial advice.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Stock trading involves risk. Always do your own research and consult with a qualified financial advisor before making investment decisions.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions, please open a GitHub issue.

## 🙏 Acknowledgments

- **Streamlit** - Web framework
- **yfinance** - Stock data API
- **pandas** - Data manipulation
- **openpyxl** - Excel export

---

Built with ❤️ using Streamlit
# stock-data-grid
