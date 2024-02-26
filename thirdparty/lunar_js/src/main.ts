import { Solar, Lunar, HolidayUtil } from 'lunar-typescript';

console.log('Hello World!');

console.log(Lunar.fromDate(new Date()).toFullString())
console.log(Solar.fromYmd(2016, 1, 1).toFullString())

console.log(HolidayUtil.getHoliday(2020, 5, 2) + '')
