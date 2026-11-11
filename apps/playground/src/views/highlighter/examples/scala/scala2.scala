package example

import scala.collection.mutable

object DocumentIndex {
  private val titles = mutable.Map.empty[Long, String]

  def put(id: Long, title: String): Unit = {
    titles.update(id, title.trim)
  }

  def find(id: Long): Option[String] = {
    titles.get(id).filter(_.nonEmpty)
  }

  def describe(ids: List[Long]): List[String] = {
    ids.flatMap { id => find(id).map(title => s"$id: $title") }
  }
}
