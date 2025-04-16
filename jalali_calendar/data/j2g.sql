create or replace function epoch_to_jd(float) RETURNS int as $$
BEGIN
    return ($1 / (24*3600) + 2440588)::int;
END;



create or replace function timestamp_to_jd(timestamp with time zone) RETURNS int as $$
BEGIN
    return epoch_to_jd(extract (epoch from $1));
END;



create or replace function date_to_jd(date) RETURNS int as $$
BEGIN
    return epoch_to_jd(extract (epoch from $1));
END;



create or replace function jalali_to_jd(int, int, int) RETURNS int as $$
DECLARE
    year alias for $1;
    month alias for $2;
    day alias for $3;
    epbase int;
    epyear int;
BEGIN
    if year >= 0 then
        epbase := year - 474;
    else
        epbase := year - 473;
    end if;
    epyear := 474 + (epbase % 2820);
    return day + 
        (month-1) * 30 + LEAST(6, month-1) + 
        ((epyear * 682 - 110) / 2816) + 
        (epyear - 1) * 365 + 
        (epbase / 2820) * 1029983 + 
        1948320;
END;




create or replace function jd_to_jalali(int) RETURNS date as $$
DECLARE
    jd alias for $1;
    year int;
    month int;
    day int;
    cycle int;
    cyear int;
    ycycle int;
    aux1 int;
    aux2 int;
    yday int;
    yday_start int;
BEGIN
    cycle := (jd - 2121446) / 1029983;
    cyear := (jd - 2121446) % 1029983;
    if cyear = 1029982 then
        ycycle := 2820;
    else
        aux1 := cyear / 366;
        aux2 := cyear % 366;
        ycycle := (2134*aux1 + 2816*aux2 + 2815) / 1028522 + aux1 + 1;
    end if;
    year := 2820*cycle + ycycle + 474;
    if year <= 0 then
        year := year - 1;
    end if;

    yday := jd - jalali_to_jd(year, 1, 1) + 1;
    
    SELECT into month, yday_start
        ind, yd
        FROM unnest(array[0, 31, 62, 93, 124, 155, 186, 216, 246, 276, 306, 336, 366])
            WITH ORDINALITY as t(yd, ind)
        where yd < yday order by yd desc limit 1;
    
    day := yday - yday_start;
    return format('%s-%s-%s', year, month, day)::date;
END;



create or replace function timestamp_to_jalali(timestamp with time zone) RETURNS date as $$
BEGIN
    return jd_to_jalali(timestamp_to_jd($1));
END;



-- select 
-- create_date,
-- replace(cast(create_date as char(60)),cast(create_date as char(10)),
-- cast(trim(concat('j',cast(jalali_to_jd(cast(substring(cast(create_date as char(10)),1,4) as int),
-- cast(substring(cast(create_date as char(10)),6,2) as int),
-- cast(substring(cast(create_date as char(10)),9,2) as int) ) as char(16))))::date
-- 	as char(10))
-- 		)::timestamp
-- from account_account


-- نام جدول account_account با جدول مورد نظر جایگزین شود
-- نام ستون create_date هم با ستون مورد نظر جایگزین شود

--datetime
update account_account
set 
create_date = 
replace(cast(create_date as char(60)),cast(create_date as char(10)),
cast(trim(concat('j',cast(jalali_to_jd(cast(substring(cast(create_date as char(10)),1,4) as int),
					cast(substring(cast(create_date as char(10)),6,2) as int),
					cast(substring(cast(create_date as char(10)),9,2) as int) ) as char(16))))::date
	as char(10))
		)::timestamp
		
--date
update account_account
set 
create_date = 
replace(cast(create_date as char(60)),cast(create_date as char(10)),
cast(trim(concat('j',cast(jalali_to_jd(cast(substring(cast(create_date as char(10)),1,4) as int),
					cast(substring(cast(create_date as char(10)),6,2) as int),
					cast(substring(cast(create_date as char(10)),9,2) as int) ) as char(16))))::date
	as char(10))
		)::date
		
		select * from account_move
		
		
		

