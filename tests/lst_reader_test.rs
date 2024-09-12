use rimseval::LSTFile;

use time::macros::datetime;

#[test]
fn test_lst_reader() {
    let file = LSTFile::open("tests/data/MCS8a_short_10k_signal.lst", 1 as u8, None).unwrap();

    assert_eq!(file.time_stamp, datetime!(2020-08-31 14:08:00.917));
    assert!(false);
}
