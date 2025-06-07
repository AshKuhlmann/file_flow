class FileSorter < Formula
  desc     "Smart CLI to organize and clean files"
  homepage "https://github.com/<ORG>/file-sorter"
  url      "https://files.pythonhosted.org/packages/<PATH>/file-sorter-1.0.0.tar.gz"
  sha256   "<FILL-IN-SHA>"
  license  "MIT"
  depends_on "python@3.12"
  def install
    system "pip3", "install", "--prefix=#{prefix}", "file-sorter==1.0.0"
  end
  test do
    system "#{bin}/file-sorter", "--help"
  end
end

