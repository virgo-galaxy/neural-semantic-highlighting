import scala.concurrent.{ExecutionContext, Future}
import scala.util.{Failure, Success, Try}

case class Document(id: Long, title: String)

def loadDocument(id: Long)(using ec: ExecutionContext): Future[Document] =
  Future(Document(id, s"Document $id"))

def loadTitles(ids: List[Long])(using ec: ExecutionContext): Future[List[String]] =
  Future.traverse(ids)(loadDocument).map(_.map(_.title))

def parseId(text: String): Either[String, Long] =
  Try(text.toLong) match
    case Success(id) => Right(id)
    case Failure(problem) => Left(problem.getMessage)
