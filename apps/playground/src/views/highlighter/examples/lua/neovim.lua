local M = {}

function M.setup(options)
  local group = vim.api.nvim_create_augroup("SourcePreview", { clear = true })
  vim.api.nvim_create_autocmd("BufWritePost", {
    group = group,
    pattern = options.pattern or "*.lua",
    callback = function(event)
      local lines = vim.api.nvim_buf_get_lines(event.buf, 0, -1, false)
      vim.schedule(function()
        vim.notify(string.format("Saved %d lines", #lines))
      end)
    end,
  })
end

return M
