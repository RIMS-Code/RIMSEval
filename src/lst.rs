//! This module reads the LST files and serves data to later write.

use anyhow::{anyhow, Result};
use time::PrimitiveDateTime;

/// Represents the bin-width of one channel of the TDC in ps.
struct BinWidth {
    value_ps: u32,
}

/// Implementation of BinWidth structure.
impl BinWidth {
    /// Create a new BinWidth from a given header.
    ///
    /// The TDC type is given as a string and can contain additional characters.
    /// It is then compared to the known TDC types.
    ///
    /// # Arguments
    /// * `header` - String slice of the header of the LST file.
    ///
    /// # Returns
    /// Result of a new bin-width structure or an error if TDC is unknown.
    fn parse_header(header: &str) -> Result<Self> {
        let value_ps: u32;

        match header.to_lowercase() {
            x if x.contains("mpa4a") => value_ps = 100,
            x if x.contains("mcs8a") => value_ps = 80,
            _ => return Err(anyhow!("Unknown TDC type: {}", header)),
        };

        Ok(Self { value_ps })
    }
}

/// Structure to hold the calibration factor.
///
/// The calibration factor is a floating point number that is used to calculate the ion range.
struct CalFactor {
    value: f64,
}

/// Implementation of the CalFactor structure.
impl CalFactor {
    /// Create a new CalFactor from a given header.
    ///
    /// The calibration factor is given as a string and can contain additional characters.
    /// It is then parsed to a floating point number.
    ///
    /// # Arguments
    /// * `header` - String slice of the header of the LST file.
    ///
    /// # Returns
    /// Result of a new calibration factor structure or an error if the calibration factor is unknown.
    fn parse_header(header: &str) -> Result<Self> {
        todo!();
    }
}

/// Enum to hold the data format of the LST file.
///
/// The data format can be either ASCII or binary.
/// The specification which oen it is is stored in the header file.
/// The following lines will be present in the header:
/// - `mpafmt=dat` -> Binary
/// - `mpafmt=asc` -> ASCII
enum DataFormat {
    ASCII,
    BINARY,
}

/// Implementation of the DataFormat enum.
impl DataFormat {
    /// Create a new DataFormat from a given header.
    ///
    /// Parse the header to find the correct data format.
    ///
    /// # Arguments
    /// * `header` - String slice of the header of the LST file.
    ///
    /// # Returns
    /// Result of a new data format enum or an error if the data format is unknown.
    fn parse_header(header: &str) -> Result<Self> {
        let data_format: Self;

        match header.to_lowercase() {
            x if x.contains("mpafmt=dat") => data_format = Self::BINARY,
            x if x.contains("mpafmt=asc") => data_format = Self::ASCII,
            _ => return Err(anyhow!("Unknown data format.")),
        };

        Ok(data_format)
    }
}

/// Structure to hold the start and stop bit of a binary range.
/// The start is inclusive while the end is exclusive.
/// This way, the range is `[start, stop)` and can be read as (start..stop).
struct BinaryRange {
    start: u32,
    stop: u32,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bin_width() {
        let bin_width = BinWidth::parse_header("[MPA4A]").unwrap();
        assert_eq!(bin_width.value_ps, 100);
        let bin_width = BinWidth::parse_header("[MCS8A A]").unwrap();
        assert_eq!(bin_width.value_ps, 80);
        let err_bin_width = BinWidth::parse_header("[MCS8B]");
        assert!(err_bin_width.is_err());
    }
}
/// Structure to hold the time patch information.
///
/// The time patch is specific for the list file and states how the data is stored.
/// The binary width is the width of the binary data in bits.
/// Following the binary width, the binary ranges for the sweep, the time, and the channel
/// are stored.
struct TimePatch {
    binary_width: u32,
    sweep_range: BinaryRange,
    time_range: BinaryRange,
    channel_range: BinaryRange,
}

/// Implementation of the TimePatch structure.
impl TimePatch {
    /// Create a new TimePatch from a given header.
    /// Header of the list file. Towards the end, the time patch is stored on a line as:
    /// `time_patch=XYZ`, where XYZ is the time_patch information. This will next be
    /// matched with the stored/known TimePatch data.
    ///
    /// # Arguments
    /// * `header` - String slice of the header of the LST file.
    ///
    /// # Returns
    /// Result of a new time patch structure or an error if the time patch is unknown.
    fn parse_header(header: &str) -> Result<Self> {
        let binary_width: u32;
        let sweep_range: BinaryRange;
        let time_range: BinaryRange;
        let channel_range: BinaryRange;

        // FIXME: Find whatever time patch is there, then match it. That way, the error gets more specific.

        match header.to_lowercase() {
            x if x.contains("time_patch=9") => {
                binary_width = 64;
                sweep_range = BinaryRange { start: 1, stop: 21 };
                time_range = BinaryRange {
                    start: 21,
                    stop: 59,
                };
                channel_range = BinaryRange {
                    start: 60,
                    stop: 64,
                };
            }
            x if x.contains("time_patch=1a") => {
                binary_width = 48;
                sweep_range = BinaryRange { start: 0, stop: 16 };
                time_range = BinaryRange {
                    start: 16,
                    stop: 44,
                };
                channel_range = BinaryRange {
                    start: 45,
                    stop: 48,
                };
            }
            _ => return Err(anyhow!("Could not find any known time patch information.")),
        };

        Ok(Self {
            binary_width,
            sweep_range,
            time_range,
            channel_range,
        })
    }
}

/// Structure to hold the data type information.
///
/// The data type is specific for the list file and states how the data is stored.
/// It contains the data format as well as the time_patch information.
/// The latter describes how to read the binary data, see, `TimePatch`.
struct DataType {
    format: DataFormat,
    time_patch: TimePatch,
}

/// Shot range structure.
/// The shot range is the range of shots that are stored in the LST file.
struct ShotRange {
    value: u32,
}

/// Implementation of the ShotRange structure.
impl ShotRange {
    /// Create a new ShotRange from a given header.
    ///
    /// The shot range is given in the header information of the LST file.
    ///
    /// # Arguments
    /// * `header` - String slice of the header of the LST file.
    ///
    /// # Returns
    /// Result of a new shot range structure or an error if the shot range is unknown.
    fn parse_header(header: &str) -> Result<Self> {
        todo!();
    }
}

/// Structure to hold the LST file data.
///
/// The LST file, as recorded by the FastComTec TDC, holds all data for a given measurement.
/// The first top rows are header information, for which we do not need too many things.
/// The data is stored at the bottom either in ASCII or binary format.
/// The data is stored in a 1D `data` vector. If the data is tagged,
/// the `data_tag` Vector will hold the tagged data.
pub struct LSTFile {
    bin_width: BinWidth,
    calibration_factor: CalFactor,
    data_type: DataType,
    shot_range: ShotRange,
    time_stamp: PrimitiveDateTime,
    data: Vec<u32>,
    data_tag: Option<Vec<u32>>,
}

/// Implementation of the LSTFile structure.
impl LSTFile {
    /// Create a new LSTFile from a given file path.
    ///
    /// The file path is the path to the LST file that should be read.
    /// The file is then read and the data is stored in the LSTFile structure.
    ///
    /// # Arguments
    /// * `file_path` - Path to the LST file.
    /// * `channel` - Channel where the signal/data is in.
    /// * `tag_channel` - Channel that contains the tag signal. If None, the data is untagged.
    ///
    /// # Returns
    /// Result of a new LSTFile structure or an error if the file could not be read.
    pub fn new(file_path: &str, channel: u8, tag_channel: Option<u8>) -> Result<Self> {
        todo!();
        // TODO:
        // 1. Read the file: and store the content in a string.
        // 2. Separate the header from the data. Separator: Line with "[DATA]".
        // 3. Parse the header for the bin width, calibration factor, data type, shot range, and
        //    time stamp.
        // 4. Test all of the above with actual LST files and ensure it works!
        // 5. Parse the data for the data, if tagged, also for the data tag and store them in their
        //    Vectors(?) and store them in their Vectors(?). (flesh this part out).
    }
}
