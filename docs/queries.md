-- latest data per symbol
select symbol, max(date)
from daily_bars
group by symbol;

