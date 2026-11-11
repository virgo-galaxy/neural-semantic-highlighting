class Document < ApplicationRecord
  belongs_to :owner
  has_many :comments, dependent: :destroy
  validates :title, presence: true, length: { maximum: 120 }

  scope :published, -> { where(published: true).order(views: :desc) }

  def self.search(term)
    published.where("title LIKE ?", "%#{sanitize_sql_like(term)}%")
  end

  def display_title
    title.presence || "Untitled document"
  end
end

records = Document.search("Surface").limit(10)
records.each { |record| puts record.display_title }
