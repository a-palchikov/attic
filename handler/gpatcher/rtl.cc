
#include <tchar.h>

// credits to Andy Polyakov (appro at fy.chalmers.se)
static void _memmove (void *dst, void *src, size_t n)
{ 
	unsigned char *d = (unsigned char*)dst, *s = (unsigned char*)src;
	while (n--) *d++ = *s++;
}

static size_t _lstrlenW (TCHAR *str)
{ 
	int len = 0;
	while (*str) { str++, len++; }
	return len;
}
 
static TCHAR *_lstrrchrW (TCHAR *str, TCHAR c)
{ 
	TCHAR *p = NULL;
	while (*str) { if (*str == c) p = str; str++; }
	return p;
}

static TCHAR *_lstrchrW (TCHAR *str,TCHAR c)
{ 
	TCHAR *p = NULL;
	while (*str) { if (*str == c) { p = str; break; } str++; }
	return p;
}

static TCHAR *_lstrncpyW (TCHAR *dst, TCHAR *src, size_t n)
{ 
	TCHAR *ret=dst;
	while(--n && *src) { *dst++ = *src++; }
	*dst=_T('\0');
	return ret;
}

