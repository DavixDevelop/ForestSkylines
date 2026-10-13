using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ImageToTreesBIN.Model
{
	public class TreesBIN
	{
		public ushort Width;
		public ushort Height;
		public int TreeCount;
		public List<ushort> ListID;
		public List<BufferedTreesCollection> Buffers;
	}

	public class BufferedTreesCollection
	{
		public ushort PosX;
		public ushort PosY;
		public List<BufferedTrees> BufferedTrees;
	}

	public class BufferedTrees
	{
		public ushort ID;
		public List<Position> Positions;
	}

	public class Position
	{
		public ushort X;
		public ushort Y;
	}
}
