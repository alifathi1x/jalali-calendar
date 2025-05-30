CREATE OR REPLACE FUNCTION public.g2j (
  in_date timestamp
)
RETURNS varchar AS
$body$
DECLARE
y smallint;
aday smallint;
amonth smallint;
ayear smallint;
value smallint;
a1 char(4);
b1 char(2);
c1 char(2);
Tday smallint;
Tmonth smallint;
Tyear smallint;
temp smallint;
CabisehYear smallint;
TMonthEnd smallint;
numdays int;
now_day timestamp without time zone;
a timestamp without time zone;
Const_Date timestamp without time zone;
BEGIN
set datestyle to MDY;
Const_Date = cast('3/21/1921' as timestamp without time zone);
--if(length(cast(in_date as text))< 14 )then
--  in_date=in_date+time '01:30';
 --return in_date;
--end if;

numdays = DATE_PART('day',in_date - Const_Date);
aday = 1;
amonth = 1;
ayear = 1300;
CabisehYear =cast((numdays / 1461) as int);
numdays = numdays - CabisehYear * 1461;
Tyear = cast((numdays / 365) as int);
If Tyear = 4 then
Tyear = Tyear - 1;
end if;
numdays = numdays - Tyear * 365;
Tmonth =cast((numdays / 31) as int);
If (Tmonth > 6) then
Tmonth = 6;
end if;
numdays = numdays - Tmonth * 31;
TMonthEnd = 0;
If (numdays >= 30 And Tmonth = 6 ) then
TMonthEnd =cast((numdays / 30) as int);
If TMonthEnd >= 5 then
TMonthEnd = 5;
end if;
numdays = numdays - TMonthEnd * 30;
End if;
Tmonth = (TMonthEnd + Tmonth);
Tday = numdays;
Tyear = (Tyear + CabisehYear * 4);
ayear = (ayear + Tyear);
amonth = amonth + Tmonth;
aday = aday + Tday;

a1 = ayear;
b1 = amonth;
c1 = aday;


If length(b1) = 1 then
b1 = '0' || b1;
end if;
If length(c1) = 1 then
c1 = '0' || c1;
end if;
return a1 || '-' || b1 || '-' || c1;
END;
$body$
LANGUAGE 'plpgsql'
VOLATILE
CALLED ON NULL INPUT
SECURITY INVOKER
COST 100;


