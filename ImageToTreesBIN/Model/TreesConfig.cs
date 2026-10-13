using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ImageToTreesBIN.Model
{
	public class TreesConfig
	{
		[JsonProperty("trees_png_path")]
		public string TreesPngPath { get; set; }

		[JsonProperty("colors_to_id")]
		public List<ColorID> ColorsID { get; set; }
	}

	public class ColorID
	{
		[JsonProperty("color")]
		public string Color { get; set; }

		[JsonProperty("id")]
		public ushort ID { get; set; }
	}
}
