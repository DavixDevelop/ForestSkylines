using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ImageToTreesBIN
{
	public class Program2
	{
		public static void Main(string[] args) {
			Console.Write("Write path to TreesBIN: ");
			string filePath = Console.ReadLine().TrimEnd();

			if(!filePath.EndsWith(".bin")) {
				Console.WriteLine("Invalid file extensions");
				Console.ReadKey();
				return;
			}

			Console.WriteLine("Reading file");

			try {
				using(var stream = File.Open(filePath, FileMode.Open)) {
					using(var reader = new BinaryReader(stream, Encoding.UTF8, false)) {
						//Read header
						var nullByte = reader.ReadByte();
						var modNameBytes = reader.ReadBytes(14);
						var modName = Encoding.UTF8.GetString(modNameBytes);
						var controlBit = reader.ReadByte();
						var author = reader.ReadChar();
						var vers = reader.ReadByte();

						if (nullByte == 0x00 && modName == "ForestSkylines" && controlBit == 0x89 && author == 'D' && vers == 0x01) {
							var mode = reader.ReadByte();
							if (mode == 0x01)
								Console.WriteLine("Mode is raster");
							else if (mode == 0x00)
								Console.WriteLine("Mode is vector");

							var width = reader.ReadUInt16();
							var height = reader.ReadUInt16();
							Console.WriteLine($"Width: {width} Height: {height}");

							var treeCount = reader.ReadInt32();
							var listIdCount = reader.ReadUInt16();
							Console.WriteLine($"Tree Count: {treeCount} ListID Count: {listIdCount}");

							Console.WriteLine("ListID: ");
							for (int t = 0; t < listIdCount; t++) {
								var treeID = reader.ReadUInt16();
								Console.Write((t != 0) ? $",{treeID}" : $"{treeID}");
							}

							Console.WriteLine();
							Console.WriteLine("Buffers: ");

							var buffersCount = reader.ReadUInt16();
							Console.WriteLine($"Buffers Count: ${buffersCount}");
							for (int b = 0; b < buffersCount; b++) {
								var bufferedTreesCount = reader.ReadUInt16();

								Console.WriteLine($"Buffered Trees Count: {bufferedTreesCount}");
								for (int i = 0; i < bufferedTreesCount; i++) {
									var treeID = reader.ReadUInt16();
									var treePositionsCount = reader.ReadUInt16();
									Console.WriteLine($"TreeID: {treeID} Positions ({treePositionsCount}): ");

									for (int p = 0; p < treePositionsCount; p++) {
										var x = (mode == 0x01) ? reader.ReadUInt16() : reader.ReadSingle();
										var y = (mode == 0x01) ? reader.ReadUInt16() : reader.ReadSingle();
										//Console.WriteLine($"{x}:{y}");
									}
								}

								Console.WriteLine();
							}
						}else {
							throw new Exception("Invalid File Header");
						}

					}
				}
			} catch (Exception ex) {
				Console.WriteLine($"There was an error parsing the .bin file: {ex.Message}");
				Console.ReadKey();
				return;
			}

			Console.WriteLine("Done!");
			Console.ReadKey();
		}
	}
}
