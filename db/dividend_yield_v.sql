create view 'dividend_yield_v' as
select a.ticker, a.date, a.dividend_per_share, b.close, round(a.dividend_per_share * 12 / b.close * 100, 2) as 'yield' from asset_dividends a
join asset_daily_price b
on a.ticker = b.ticker and a.date = b.date