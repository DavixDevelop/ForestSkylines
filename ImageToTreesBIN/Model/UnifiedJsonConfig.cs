using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ImageToTreesBIN.Model
{
	public class UnifiedJsonConfig
	{
		[JsonProperty("id_list")]
		public List<ushort> ListID { get; set; }

		[JsonProperty("color_to_id")]
		public List<string> ColorToID { get; set; }

		[JsonProperty("trees_bin_path")]
		public string TreesBinPath { get; set; }

		[JsonProperty("raster")]
		public RasterConfig RasterConfig { get; set; }
	}

	public class RasterConfig {
		[JsonProperty("png_path")]
		public string TreesPngPath { get; set; }
	}
}
