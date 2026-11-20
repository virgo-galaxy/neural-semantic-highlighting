module Documents
  class Document
    attr_reader :id, :title
    attr_accessor :views

    def initialize(id:, title:, views: 0)
      @id = id
      @title = title.strip
      @views = views
    end

    def visit!
      @views += 1
      self
    end

    def to_h = { id: @id, title: @title, views: @views }
  end
end

record = Documents::Document.new(id: 1, title: "Overview")
puts record.visit!.to_h
