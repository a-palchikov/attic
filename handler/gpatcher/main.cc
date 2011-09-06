
#include <AH6X_HAPI.h>
#include <windows.h>
#include <tchar.h>
#include "mini_disassembler.h"

/*
	Compile with -Ox -Gd -Zl -GF -MD -Zi -Oy- -DUNICODE main.cc argvargc.cc mini_disassembler.cc ia32_opcode_map.cc ia32_modrm_map.cc <additional libs> /link /INCREMENTAL:NO /OPT:REF

	Notes:
	Ox - favour speed over size
	Gd - cdecl for all functions except c++ and those explicitly specified
	Zl - omit default library
	GF - pool strings as RO
	MD - multithreaded DLL version of runtime 
	LD - create DLL
*/

#pragma comment(linker, "/entry:_mainCRTStartup")
#pragma comment(linker, "/SUBSYSTEM:CONSOLE")
#pragma comment(linker, "/defaultlib:kernel32.lib")

extern int _ConvertCommandLineToArgcArgv();
extern TCHAR *_ppszArgv[];

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

typedef VOID (NTAPI *pfnKiUserExceptionDispatcher)(PEXCEPTION_RECORD ExceptionRecord, PCONTEXT Context);
typedef BOOL (NTAPI *pfnRtlDispatchException)(PEXCEPTION_RECORD ExceptionRecord, PCONTEXT Context);

#pragma data_seg(".patched")
BYTE OldRtlDispatchException[AH6X_HAPI_SZ_APISAVE] = {0};
BYTE RtlDispatchExceptionTrampoline[AH6X_HAPI_SZ_APICALL] = {0};
BYTE OldUnhandledExceptionFilter[AH6X_HAPI_SZ_APISAVE] = {0};
BYTE UnhandledExceptionFilterTrampoline[AH6X_HAPI_SZ_APICALL] = {0};
#pragma data_seg()
#pragma comment(linker, "/SECTION:.patched,RWE")

#if defined(WIN32) && !defined(_WIN32)
#define _WIN32
#endif

#if defined(WIN32) && !defined(_X86)
#define _X86
#endif

namespace gonzo {
	LONG __stdcall exception_handler(PEXCEPTION_POINTERS /*ExceptionInfo*/)
	{
		// ap(todo): implement
		return EXCEPTION_CONTINUE_SEARCH;
	}
}

namespace {
	// KiUserExceptionDispatcher
	// returns in %al
	BOOL __RtlDispatchException(PEXCEPTION_RECORD ExceptionRecord, PCONTEXT Context)
	{
		pfnRtlDispatchException fn = (pfnRtlDispatchException)(PBYTE)RtlDispatchExceptionTrampoline;
		if (!fn(ExceptionRecord, Context)) {
			// unhandled
			EXCEPTION_POINTERS exceptPtrs;
			exceptPtrs.ExceptionRecord = ExceptionRecord;
			exceptPtrs.ContextRecord = Context;
			gonzo::exception_handler(&exceptPtrs);
		}
		// _always_ return `handled'
		return TRUE;
	}

	LONG __UnhandledExceptionFilter(PEXCEPTION_POINTERS /*ExceptionInfo*/)
	{
		/* UnhandledExceptionFilter is disabled in its entirety since it messes things up
		when invoked from RtlExceptionDispatch() and leads to WER dialog appearing when WER is enabled
		even though we _always_ handle the unhandled exception
		ap(todo): based on some *configuration* option set, let the invocation still fallback to old
		functionality to run errands like invoking the JIT debugger and such (...)
		*/
		return EXCEPTION_CONTINUE_EXECUTION;
	}

	// returns reladdr of RtlExceptionDispatch, or 0 if none found
	unsigned int find_RtlDispatchException(HMODULE hNative)
	{
		unsigned char *kiUserExceptionDispatcher = (unsigned char *)::GetProcAddress(hNative, "KiUserExceptionDispatcher");
#ifdef _X86
		using namespace sidestep;
		MiniDisassembler disasm(true, true); // 32-bit mode
		InstructionType instr = IT_UNUSED;
		unsigned int bytes = 0;
		while(IT_RETURN != instr && IT_JUMP != instr) {
			instr = disasm.Disassemble(kiUserExceptionDispatcher + bytes, bytes);
		}
		if (IT_JUMP == instr && 0xe8 == *(char *)(kiUserExceptionDispatcher + bytes)) {
			// found a call
			return *(unsigned int *)(kiUserExceptionDispatcher + bytes + 1);
		}
		return 0;
#else
#error "No disassembler for specified architecture!"
#endif		
	}

	BOOL patch()
	{
		HMODULE hNative = ::GetModuleHandleW(L"ntdll.dll");
		if (!hNative) {
			//Log_Fatal("ntdll module unmapped in current process");
			return FALSE;
		}
		HMODULE hKernel32 = ::GetModuleHandleW(L"kernel32.dll");
		if (!hKernel32) {
			//Log_Fatal("kernel32 module unmapped in current process");
			return FALSE;
		}

		unsigned int rtlDispatchException = find_RtlDispatchException(hNative);
		if (!rtlDispatchException) {
			//Log_Fatal("Failed to locate RtlExceptionDispatch");
			return FALSE;
		}
		LONG hookResult = AH6X_HookApi(AH6X_HAPI_FL_OWR|AH6X_HAPI_FL_ADDRESS,
					  0,
					  (LPCSTR)rtlDispatchException,
					  OldRtlDispatchException,
					  RtlDispatchExceptionTrampoline,
					  __RtlDispatchException
					);
		hookResult = AH6X_HookApi(AH6X_HAPI_FL_OWR|AH6X_HAPI_FL_HMODULE,
					  (LPCWSTR)hKernel32,
					  "UnhandledExceptionFilter",
					  OldUnhandledExceptionFilter,
					  UnhandledExceptionFilterTrampoline,
					  __UnhandledExceptionFilter
					);

		return TRUE;
	}

	int main(int argc, wchar_t *argv[])
	{
		if (!patch()) {
			// if patching failed, go the UnhandledExceptionFilter route
			::SetUnhandledExceptionFilter(gonzo::exception_handler);
		}

		return 0;
	}
}

void _mainCRTStartup()
{
	int argc = _ConvertCommandLineToArgcArgv();
	int result = main(argc, _ppszArgv);
	::ExitProcess(result);
}

