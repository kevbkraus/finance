CREATE TABLE "asset_dividends" (
	"ticker"	TEXT,
	"date"	TEXT,
	"dividend_per_share"	NUMERIC,
	PRIMARY KEY("ticker","date")
)