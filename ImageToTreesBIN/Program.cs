using ImageToTreesBIN.Model;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ImageToTreesBIN
{
	public class Program
	{
		static void Main(string[] args) {
			Console.Write("Enter path to config file: ");
			string configFilePath = Console.ReadLine();
			DateTime start = DateTime.Now;

			if (configFilePath == null) {
				Console.WriteLine("No config file path specified");
				Console.ReadKey();
				return;
			}

			UnifiedJsonConfig jsonConfig = null;

			try {
				Console.WriteLine($"Parsking config file: {Path.GetFileName(configFilePath)}");
				using (StreamReader configFile = File.OpenText(configFilePath)) {
					JsonSerializer serializer = new JsonSerializer();
					jsonConfig = (UnifiedJsonConfig)serializer.Deserialize(configFile, typeof(UnifiedJsonConfig));
				}
			}catch(Exception ex) {
				Console.WriteLine($"There was an error while parsing config file: {ex.Message}.\nPlease make sure the config is a valid json file");
				Console.ReadKey();
				return;
			}

			if(jsonConfig == null) {
				Console.WriteLine("Empty config file");
				Console.ReadLine();
				return;
			}

			if(!jsonConfig.TreesBinPath.EndsWith(".bin")) {
				Console.WriteLine("The key 'trees_bin_path' in the config file must end with a .bin and be a valid file path");
				Console.ReadKey();
				return;
			}

			if(!jsonConfig.RasterConfig.TreesPngPath.EndsWith(".png")) {
				Console.WriteLine("The key`vector.png_path` in the config file must end with a .png and be a valid file path");
				Console.ReadKey();
				return;
			}

			int tileSize = 512;
			string rootPath = Path.GetDirectoryName(jsonConfig.RasterConfig.TreesPngPath);

			if(jsonConfig.ListID.Count != jsonConfig.ColorToID.Count) {
				Console.WriteLine($"The key 'id_list' and 'color_to_id' in the config must have the same count of items ({jsonConfig.ListID.Count} != {jsonConfig.ColorToID.Count})");
				Console.ReadKey();
				return;
			}

			TreesBIN treesBIN = new TreesBIN { TreeCount = 0, ListID = new List<ushort>(), Buffers = new List<BufferedTreesCollection>()};

			Dictionary<string, ushort> colorID = new Dictionary<string, ushort>();
			ushort col_id;
			string col_hex;
			for (int i = 0; i < jsonConfig.ListID.Count; i++) {
				col_id = jsonConfig.ListID[i];
				col_hex = jsonConfig.ColorToID[i];

				if (!TryParseColor(col_hex, out string hex)) {
					Console.WriteLine($"Invalid color hex: {col_hex} for ID: {col_id}\n in config file");
					Console.ReadKey();
					return;
				}

				colorID.Add(hex, col_id);
				treesBIN.ListID.Add(col_id);
			}

			string colorHex;
			short id;
			BufferedTrees bufferedTrees = new BufferedTrees();

			Console.WriteLine($"Parsing PNG image: {Path.GetFileName(jsonConfig.RasterConfig.TreesPngPath)}");
			try {
				using (var fileStream = File.OpenRead(jsonConfig.RasterConfig.TreesPngPath)) {
					var bitmap = new Bitmap(fileStream);

					int width = bitmap.Width;
					int height = bitmap.Height;
					treesBIN.Width = (ushort)width;
					treesBIN.Height = (ushort)height;

					Rectangle rect;

					bool skip = false;
					if (!skip) {

						for (int tileY = 0; tileY < height; tileY += tileSize) {
							for (int tileX = 0; tileX < width; tileX += tileSize) {
								int tileWidth = Math.Min(tileSize, width - tileX);
								int tileHeight = Math.Min(tileSize, height - tileY);

								rect = new Rectangle(tileX, tileY, tileWidth, tileHeight);

								using (var tileBitmap = bitmap.Clone(rect, bitmap.PixelFormat)) {
									ProcessTile(tileBitmap, tileWidth, tileHeight, tileX, tileY, width, height, colorID, ref bufferedTrees, ref treesBIN);
								}
							}
						}

					}

				}
			}catch(Exception ex) {
				Console.WriteLine($"There was an error reading the PNG image: {ex.Message}");
				Console.ReadKey();
				return;
			}

			//treesBIN.Buffers != null && treesBIN.Buffers.Count > 0 && rootPath != null
			if (treesBIN.Buffers != null && rootPath != null) {
				Console.WriteLine($"Generating {Path.GetFileName(jsonConfig.RasterConfig.TreesPngPath)} file...");

				//Write data structure as binary file
				using (var stream = File.Open(jsonConfig.TreesBinPath, FileMode.Create)) {
					using (var writer = new BinaryWriter(stream, Encoding.UTF8, false)) {
						//File Header
						writer.Write((byte)0x00);
						writer.Write(Encoding.UTF8.GetBytes("ForestSkylines"));
						writer.Write((byte)0x89);
						writer.Write('D');
						writer.Write((byte)0x01);

						//Data Block
						//1 as raster mode 
						writer.Write((byte)0x01);
						//Width and height of raster
						writer.Write(treesBIN.Width); //Offset 0x01
						writer.Write(treesBIN.Height); //Offset 0x03
						//Tree count
						writer.Write(treesBIN.TreeCount); //Offset 0x05

						//Write list ID count
						writer.Write((ushort)treesBIN.ListID.Count); //Offset 0x09
						foreach (ushort _id in treesBIN.ListID)
							writer.Write(_id); //Offset 0x0b

						//Write buffers count
						writer.Write((ushort)treesBIN.Buffers.Count); //Offset 0x0d
						//Write buffers
						foreach (BufferedTreesCollection col in treesBIN.Buffers) {
							//Write buffered trees count
							writer.Write((ushort)col.BufferedTrees.Count); //Offset 0x11
							//Write buffered trees
							foreach (BufferedTrees trees in col.BufferedTrees) {
								//Write ID and count of positions
								writer.Write(trees.ID); //Offset 0x13
								writer.Write((ushort)trees.Positions.Count); //0x15

								//Write pixel position location within image
								foreach (Position position in trees.Positions) {
									//Write X and Y pixel location
									writer.Write(position.X); //Offset 0x1a
									writer.Write(position.Y); //Offset 0x1b
								}
							}

							writer.Flush();
						}

						writer.Flush();
					}
				}
			} else {
				Console.WriteLine("No matching pixel colors were found in the PNG image");
				Console.ReadKey();
				return;
			}
			

			TimeSpan totalTime = DateTime.Now - start;
			Console.WriteLine($"Done in {totalTime.ToString(@"mm\:ss")}");
			Console.ReadKey();
		}

		public static bool TryParseColor(string hexColor, out string hex) {
			hex = null;

			if (string.IsNullOrEmpty(hexColor))
				return false;

			hexColor = hexColor.Trim().Replace("#", "");

			if (hexColor.Length != 6 && hexColor.Length != 8)
				return false;

			if(int.TryParse(hexColor, System.Globalization.NumberStyles.HexNumber, System.Globalization.CultureInfo.InvariantCulture, out _))
			{
				hex = hexColor.ToUpperInvariant();
				return true;
			}

			return false;
		}
		
		public static void ProcessTile(Bitmap bitmap, int tileWidth, int tileHeight, int tileX, int tileY, int width, int height, Dictionary<string, ushort> colorID, ref BufferedTrees bufferedTrees, ref TreesBIN treesBIN) {
			var rect = new Rectangle(0, 0, tileWidth, tileHeight);
			BitmapData bitmapData = bitmap.LockBits(rect, ImageLockMode.ReadOnly, bitmap.PixelFormat);

			try {
				var ptr = bitmapData.Scan0;
				int bytesCount = bitmapData.Stride * tileHeight;
				string colorHex;
				int rowOffset, pixelOffset;
				byte r, g, b, a;
				ushort id;

				BufferedTreesCollection _col = new BufferedTreesCollection() { PosX = (ushort)tileX, PosY = (ushort)(height - tileY), BufferedTrees = new List<BufferedTrees>() };
				Dictionary<string, BufferedTrees> colBufferedTrees = new Dictionary<string, BufferedTrees>();

				unsafe {
					ReadOnlySpan<byte> pixelsSpan = new ReadOnlySpan<byte>((void*)ptr, bytesCount);

					for (int y = 0; y < tileHeight; y++) {
						rowOffset = y * bitmapData.Stride;

						for (int x = 0; x < tileWidth; x++) {
							//Each pixel is 4 bits wide and in BGRA format
							pixelOffset = rowOffset + (x * 4);
							b = pixelsSpan[pixelOffset];
							g = pixelsSpan[pixelOffset + 1];
							r = pixelsSpan[pixelOffset + 2];
							a = pixelsSpan[pixelOffset + 3];

							if (a == 0)
								continue;

							colorHex = $"{r:X2}{g:X2}{b:X2}";

							if (colorID.TryGetValue(colorHex, out id)) {

								if (!colBufferedTrees.TryGetValue(colorHex, out bufferedTrees)) {
									bufferedTrees = new BufferedTrees { ID = id, Positions = new List<Position>()};
									colBufferedTrees.Add(colorHex, bufferedTrees);
								}

								bufferedTrees.Positions.Add(new Position() { X = (ushort)(tileX + x), Y = (ushort)(height - (tileY + y) - 1)});
								treesBIN.TreeCount++;
								colBufferedTrees[colorHex] = bufferedTrees;
							}
						}
					}

				}

				foreach (string col in colBufferedTrees.Keys) {
					bufferedTrees = colBufferedTrees[col];
					_col.BufferedTrees.Add(bufferedTrees);
				}

				if (_col.BufferedTrees.Count > 0)
					treesBIN.Buffers.Add(_col);

			} finally {
				bitmap.UnlockBits(bitmapData);
			}
		}
	}


}
