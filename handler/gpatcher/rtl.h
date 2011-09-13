
extern "C" {
	void _memmove (void *dst, void *src, size_t n);
	size_t _lstrlenW (TCHAR *str);
	TCHAR *_lstrrchrW (TCHAR *str, TCHAR c);
	TCHAR *_lstrchrW (TCHAR *str,TCHAR c);
	TCHAR *_lstrncpyW (TCHAR *dst, TCHAR *src, size_t n);
}
