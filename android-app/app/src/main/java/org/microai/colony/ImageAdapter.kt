package org.microai.colony

import android.content.Context
import android.graphics.BitmapFactory
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import androidx.recyclerview.widget.RecyclerView
import java.io.File

class ImageAdapter(private val ctx: Context) : RecyclerView.Adapter<ImageAdapter.VH>() {
    private var items: List<File> = emptyList()
    fun submitList(list: List<File>) { items = list; notifyDataSetChanged() }
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val v = LayoutInflater.from(parent.context).inflate(org.microai.colony.R.layout.item_image, parent, false)
        return VH(v)
    }
    override fun getItemCount(): Int = items.size
    override fun onBindViewHolder(holder: VH, position: Int) {
        val f = items[position]
        val bmp = BitmapFactory.decodeFile(f.absolutePath)
        holder.img.setImageBitmap(bmp)
    }
    class VH(v: View) : RecyclerView.ViewHolder(v) { val img: ImageView = v.findViewById(org.microai.colony.R.id.item_image) }
}
